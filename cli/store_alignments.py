import sys
sys.path.insert(1, '../')
from webapp import db
from io import StringIO
from webapp.models import Entry, Link, Translation, Retrieval
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
from utils import detok, process, create_stringio
from tools.align import BLEUAligner
from tqdm import tqdm
#langs = ['en', 'ml', 'ur', 'te', 'hi', 'pa', 'kn', 'or', 'as', 'gu', 'mr', 'ta', 'bn']

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
translator.cuda()
aligner = BLEUAligner(translator, tokenizer, segmenter)


langs = ['ml', 'ur', 'te', 'hi', 'ta', 'bn']
src_lan = 'hi' 
tgt_lan = 'en'
src_file = open('pib_en-{}.{}.txt'.format(src_lan,src_lan),'a')
tgt_file = open('pib_en-{}.{}.txt'.format(src_lan,tgt_lan),'a')

def paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, q_id, r_id):
    print('##########Article {} #########'.format(q_id),file=src_file)
    print(src_entry,file=src_file)
    print('##########Article {} #########'.format(r_id),file=tgt_file)
    print(tgt_entry,file=tgt_file)

def init_align():
    ids = db.session.query(Retrieval)
    for i in tqdm(ids):
        q = i.query_id
        r = i.retrieved_id
        qlang = db.session.query(Entry.lang).filter(Entry.id==q).first().lang
        score = i.score
        date_link = db.session.query(Link.second_id).filter(Link.first_id==q).distinct().all()
        for link in date_link:
            rlang = db.session.query(Entry.lang).filter(Entry.id==link.second_id).first().lang
            if rlang=='en' and qlang=='{}'.format(src_lan) and link.second_id==r:

                src = db.session.query(Entry.content, Entry.lang).filter(Entry.id==q).first()
                tgt = db.session.query(Entry.content, Entry.lang).filter(Entry.id==r).first()

                hyp = db.session.query(Translation.translated).filter(Translation.parent_id==q)\
                                .first().translated

                src_tokenized , src_io = process(src.content, src.lang)
                tgt_tokenized , tgt_io = process(tgt.content, tgt.lang)
                hyp_io = StringIO(hyp)
                src_aligned , tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io)
                
                src_aligned = detok(src_aligned)
                tgt_aligned = detok(tgt_aligned)               
                src_entry = '\n'.join(src_aligned)
                tgt_entry = '\n'.join(tgt_aligned)

                paralle_write(src_entry, src.lang, tgt_entry, tgt.lang, q, r)

if __name__ == '__main__':
    init_align()
