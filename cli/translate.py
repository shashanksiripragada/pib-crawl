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
#from utils import process, create_stringio
from ilmulti.utils.language_utils import inject_token
from utils import BatchBuilder
from collections import defaultdict

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
translator.cuda()

langs = ['hi','ml','bn','te','ta','ur']
model = 'mm_all'
error = open('translate_error.txt','w+')

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
            mapping[int(uid[0])].append(int(uid[1]))

        start = 0 
        for entry_id in mapping:
            num_lines = len(mapping[entry_id])
            translated = hyps[start:start+num_lines]
            print(translated)
            start = num_lines

            entry = Translation(parent_id= entry_id, model= model, lang= tgt_lang, translated= translated)
            try:
                db.session.add(entry)
                db.session.commit()
            except:
                print(entry.id,fp=error)

        #print(ids,batch.uids)
        #translated = '\n'.join(hyps)
        #print(translated)


if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('max_tokens',type=int)
    args = parser.parse_args()
    translate(args.max_tokens)




#if entry.content:
#    exists = Translation.query.filter(Translation.parent_id==entry.id).first()
#    if not exists:
#        src_tokenized, src_io = process(entry.content, entry.lang)
#        injected_src_tokenized = inject_token(src_tokenized, tgt_lang)

