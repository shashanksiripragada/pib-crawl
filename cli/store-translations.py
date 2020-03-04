import sys
sys.path.insert(1, '../')
from webapp import db
from webapp.models import Entry, Link, Translation, Retrieval
from sqlalchemy import and_
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from tqdm import tqdm
from argparse import ArgumentParser
from ilmulti.utils.language_utils import inject_token
from utils import BatchBuilder
from sqlalchemy import or_, and_
from collections import defaultdict
from cli import ILMULTI_DIR


def translate(segmenter, tokenizer, translator, max_tokens, model, langs, tgt_lang = 'en', rebuild=False):     
    entries = db.session.query(Entry.id,Entry.lang,Entry.date,Entry.content)\
                .filter(Entry.lang.in_(langs)).all()
    
    
    def exists(entry):
        if rebuild:
            return False
        translation = Translation.query.filter(and_(Translation.parent_id==entry.id,\
                                Translation.model==model)).first() 

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
                translation = Translation.query.filter(and_(Translation.parent_id==entry_id,Translation.model==model)).first()
                
                def modf(entry):
                    db.session.add(entry)
                    db.session.commit()
                    #print(entry_id,file=sys.stderr)

                if translation is not None:
                    translation.translated = translated
                    modf(translation)

                else:
                    entry = Translation(parent_id= entry_id, model= model, lang= tgt_lang, translated= translated)            
                    modf(entry)


if __name__ == '__main__':
    langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']
    #model = 'mm_all_iter0'
    langs = ['or']
    segmenter = Segmenter()
    tokenizer = SentencePieceTokenizer()
    root = os.path.join(ILMULTI_DIR, 'mm-all')
    translator = mm_all(root=root, use_cuda=True).get_translator()

    parser=ArgumentParser()
    parser.add_argument('--max_tokens', type=int, help='max_tokens in each batch', required=True)
    parser.add_argument('--model', help='model used to translate', required=True)
    parser.add_argument('--tgt_lang', help='target lang to translate to', required=True)
    parser.add_argument('--rebuild', help='restore the tranlsation items', action='store_true')
    args = parser.parse_args()
    translate(segmenter, tokenizer, translator, args.max_tokens,\
             args.model, langs, args.tgt_lang, args.rebuild)
