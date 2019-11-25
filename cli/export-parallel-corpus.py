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
from argparse import ArgumentParser
from sqlalchemy import func, and_
#langs = ['en', 'ml', 'ur', 'te', 'hi', 'pa', 'kn', 'or', 'as', 'gu', 'mr', 'ta', 'bn']

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root, use_cuda=True).get_translator()
aligner = BLEUAligner(translator, tokenizer, segmenter)


langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']

def paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, q_id, r_id):
    print('##########Article {} #########'.format(q_id),file=src_file)
    print(src_entry,file=src_file)
    print('##########Article {} #########'.format(r_id),file=tgt_file)
    print(tgt_entry,file=tgt_file)

def export(src_lang, tgt_lang, model):
    ids = db.session.query(Retrieval).filter(Retrieval.model==model).all()
    for i in tqdm(ids):
        q = i.query_id
        r = i.retrieved_id
        qlang = db.session.query(Entry.lang).filter(Entry.id==q).first().lang
        score = i.score
        date_link = db.session.query(Link.second_id).filter(Link.first_id==q).distinct().all()
        for link in date_link:
            rlang = db.session.query(Entry.lang).filter(Entry.id==link.second_id).first().lang
            if rlang==tgt_lang and qlang=='{}'.format(src_lang) and link.second_id==r:

                src = db.session.query(Entry.content, Entry.lang).filter(Entry.id==q).first()
                tgt = db.session.query(Entry.content, Entry.lang).filter(Entry.id==r).first()

                hyp = db.session.query(Translation.translated).\
                        filter(and_(Translation.parent_id==q, Translation.model==model))\
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
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    #parser.add_argument('src_file', help='src file to write the alignments into')
    #parser.add_argument('src_file', help='src file to write the alignments into')
    args = parser.parse_args()
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    src_file = open('pib_en-{}.{}.txt'.format(src_lang, src_lang),'a')
    tgt_file = open('pib_en-{}.{}.txt'.format(src_lang, tgt_lang),'a')
    model = 'mm_all_iter0'
    export(src_lang, tgt_lang, model)

