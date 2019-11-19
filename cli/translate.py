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

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root, use_cuda=True).get_translator()


langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']
model = 'mm_all_iter0'
error = open('translate_error.txt','a')

def translate(max_tokens):        
    entries = db.session.query(Entry.id,Entry.lang,Entry.date,Entry.content)\
                .filter(Entry.lang.in_(langs)).all()
    tgt_lang = 'en'
    batches = BatchBuilder(entries, max_tokens, tgt_lang)
    for batch in tqdm(batches):
        generation_output = translator(batch.lines)        
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
            start = num_lines
            exists = Translation.query.filter(and_(Translation.parent_id==entry_id,Translation.model==model)).first()
            if not exists:
                translated = '\n'.join(translated)
                entry = Translation(parent_id= entry_id, model= model, lang= tgt_lang, translated= translated)            
                try:
                    db.session.add(entry)
                    db.session.commit()
                except:
                    print(entry_id,file=error)


if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('max_tokens',type=int)
    args = parser.parse_args()
    translate(args.max_tokens)
