import sys
sys.path.insert(1, '../')
from webapp import db
from webapp.models import Entry, Link, Translation, Retrieval
from sqlalchemy import and_
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from tqdm import tqdm
from utils import process, create_stringio
from ilmulti.utils.language_utils import inject_token

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
translator.cuda()

langs = ['hi','ml','bn','te','ta','ur']
model = 'mm_all'
error = open('translate_error.txt','w+')

def translate():        
    entries = db.session.query(Entry.id,Entry.lang,Entry.date,Entry.content)\
                .filter(Entry.lang.in_(langs)).all()
    tgt_lang = 'en'
    for entry in tqdm(entries):
        if entry.content:
            exists = Translation.query.filter(Translation.parent_id==entry.id).first()
            if not exists:
                '''
                src_tok = inject_lang_token(entry.content,tgt_lang=tgt_lang)
                out = translator(src_tok)
                hyps = [ gout['tgt'] for gout in out ]
                hyps = detok(hyps)
                translated = '\n'.join(hyps)
                '''
                src_tokenized, src_io = process(entry.content, entry.lang)
                injected_src_tokenized = inject_token(src_tokenized, tgt_lang)

                generation_output = self.model(injected_src_tokenized)

                hyps = [ gout['tgt'] for gout in generation_output ]

                entry = Translation(parent_id= entry.id, model= model, lang= tgt_lang, translated= translated)
                try:
                    db.session.add(entry)
                    db.session.commit()
                except:
                    print(entry.id,fp=error)

if __name__ == '__main__':
    translate()