import os
import sys
from tqdm import tqdm
from argparse import ArgumentParser
from collections import defaultdict
from ilmulti.translator import from_pretrained

from sqlalchemy import or_, and_

# Internal imports.
from .. import db
from ..models import Entry, Link, Translation
from .utils import BatchBuilder

def delete_existing_translations(model, tgt_lang):
    translations = Translation.query.filter(and_(
        Translation.model == model,
        Translation.lang == tgt_lang))

    translations.delete()
    db.session.commit()

def translate(engine, max_tokens, model, langs, tgt_lang = 'en', force_rebuild=False):     
    segmenter = engine.segmenter
    translator = engine.translator
    tokenizer = engine.tokenizer

    query = (
        db.session.query(
            Entry.id, Entry.lang, Entry.date, Entry.content
        ).filter(Entry.lang.in_(langs)) 
    )


    def exists(entry):
        if force_rebuild:
            return False

        translation = (
            Translation.query.filter(
                and_(
                    Translation.parent_id == entry.id,
                    Translation.model == model,
                    Translation.lang == tgt_lang
                )
            ).first()
        )

        return True if translation else False

    total = query.count()
    entries = query.all()
    batches = BatchBuilder(segmenter, tokenizer, entries, max_tokens, tgt_lang, filter_f=exists)

    with tqdm(total=total) as pbar:
        for batch in batches:
            pbar.update(n=batch.state['epb'])
            pbar.set_postfix(batch.state)

            # Translate
            generation_output = translator(batch.lines)        

            # Collect
            hyps = [ gout['tgt'] for gout in generation_output ]
            hyp_ids = [ gout['id'] for gout in generation_output ]
            collector = defaultdict(list)
            for id, hyp in zip(hyp_ids, hyps):
                uid = batch.uids[id]
                idx, line_num = uid.split()
                line_num = int(line_num)
                collector[idx].append((line_num, hyp))

            for idx in collector:
                sorted_lines = sorted(collector[idx])
                line_numbers, ordered_lines = list(zip(*sorted_lines))
                translated = '\n'.join(ordered_lines)

                entry_id = int(idx)

                translation = (
                    Translation.query.filter(
                        and_(
                            Translation.parent_id==entry_id, 
                            Translation.model==model,
                            Translation.lang == tgt_lang
                        )
                    ).first()
                )

                # Converting entry_id to Integer.
                # This can silently fail.
                
                def modify_translation(entry):
                    db.session.add(entry)
                    db.session.commit()

                if translation is not None:
                    if translated != translation.translated:
                        print(entry_id, "Different translations!")
                    translation.translated = translated
                    modify_translation(translation)

                else:
                    entry = Translation(
                        parent_id=entry_id, model=model,
                        lang=tgt_lang, translated=translated
                    )            
                    modify_translation(entry)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--max-tokens', type=int, help='max tokens in each batch', required=True)
    parser.add_argument('--model', help='model used to translate', required=True)
    parser.add_argument('--tgt-lang', help='target lang to translate to', required=True)
    parser.add_argument('--force-rebuild', help='restore the tranlsation items', action='store_true')
    parser.add_argument('--start-over', help='delete existing translations', action='store_true')
    parser.add_argument('--resume-from', help='delete existing translations', action='store_true')
    parser.add_argument('--use-cuda', help='use available GPUs', action='store_true')

    args = parser.parse_args()

    if args.start_over:
        delete_existing_translations(args.model, args.tgt_lang)

    engine = from_pretrained(tag=args.model, use_cuda=args.use_cuda)
    langs = ['hi', 'ta', 'te', 'ml', 'bn', 'gu', 'mr', 'pa', 'or', 'ur'] 

    translate(
        engine, args.max_tokens, 
        args.model, langs, args.tgt_lang,
        args.force_rebuild
    )
