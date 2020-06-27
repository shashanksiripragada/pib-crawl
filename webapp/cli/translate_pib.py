import os
import sys

from webapp import db
from webapp.models import Entry, Link, Translation
from sqlalchemy import and_

from tqdm import tqdm
from argparse import ArgumentParser
from .utils import BatchBuilder
from sqlalchemy import or_, and_
from collections import defaultdict
from ilmulti.translator import from_pretrained


def translate(engine, max_tokens, model, langs, tgt_lang = 'en', force_rebuild=False):     
    segmenter = engine.segmenter
    translator = engine.translator
    tokenizer = engine.tokenizer

    entries = (
        db.session.query(
            Entry.id, Entry.lang, Entry.date, Entry.content
        ).filter(Entry.lang.in_(langs)).all()
    )

    def exists(entry):
        if force_rebuild:
            return False

        translation = (
            Translation.query.filter(
                and_(
                    Translation.parent_id == entry.id,
                    Translation.model == model
                )
            ).first()
        )

        return True if translation else False

    batches = BatchBuilder(segmenter, tokenizer, entries, max_tokens, tgt_lang, filter_f=exists)

    with tqdm(total=len(entries)) as pbar:
        for batch in batches:
            pbar.update(n=batch.state['epb'])
            # print(batch.state['epb'])
            pbar.set_postfix(batch.state)

            # Translate
            generation_output = translator(batch.lines)        

            # Collect
            hyps = [ gout['tgt'] for gout in generation_output ]
            ids = [ gout['id'] for gout in generation_output ]
            mapping = defaultdict(list)
            for uid in batch.uids:
                uid = uid.split()
                idx, line_num = int(uid[0]), int(uid[1])
                mapping[idx].append(line_num)

            start = 0 
            for entry_id in mapping:
                num_lines = len(mapping[entry_id])
                translated = hyps[start:start+num_lines]
                translated = '\n'.join(translated)
                start = num_lines
                translation = (
                    Translation.query.filter(
                        and_(
                            Translation.parent_id==entry_id, 
                            Translation.model==model
                        )
                    ).first()
                )
                
                def modify_entry(entry):
                    db.session.add(entry)
                    db.session.commit()

                if translation is not None:
                    translation.translated = translated
                    modify_entry(translation)

                else:
                    entry = Translation(
                        parent_id=entry_id, model=model,
                        lang=tgt_lang, translated=translated
                    )            
                    modify_entry(entry)


if __name__ == '__main__':
    langs = ['hi', 'ta', 'te', 'ml', 'bn', 'gu', 'mr', 'pa', 'or'] 

    parser=ArgumentParser()
    parser.add_argument('--max_tokens', type=int, help='max_tokens in each batch', required=True)
    parser.add_argument('--model', help='model used to translate', required=True)
    parser.add_argument('--tgt-lang', help='target lang to translate to', required=True)
    parser.add_argument('--force-rebuild', help='restore the tranlsation items', action='store_true')
    args = parser.parse_args()
    engine = from_pretrained(tag=args.model)
    translate(engine, args.max_tokens, args.model, langs, args.tgt_lang, args.force_rebuild)
