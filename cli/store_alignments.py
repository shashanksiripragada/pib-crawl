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
#langs = ['en', 'ml', 'ur', 'te', 'hi', 'pa', 'kn', 'or', 'as', 'gu', 'mr', 'ta', 'bn']

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root, use_cuda=True).get_translator()
aligner = BLEUAligner(translator, tokenizer, segmenter)


langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']

def store_aligned_date(src_lang, tgt_lang):
    ids = db.session.query(Retrieval)
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
'''
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
    store_aligned(src_lang, tgt_lang)
'''
#from webapp.retrieval import get_candidates, retrieve_neighbours_en


def get_match(src_id, threshold):
    thresh=threshold
    retrieved = db.session.query(Retrieval).filter(Retrieval.query_id==src_id)\
                          .first()
    link = db.session.query(Link).filter(Link.first_id==src_id).distinct().all()

    if retrieved and (link==[]):
        if retrieved.score >= thresh:
            return retrieved.retrieved_id

def align_pairs(src_id, tgt_id):
    # assuming src is non-en 
    src = db.session.query(Entry.content, Entry.lang).filter(Entry.id==src_id).first()
    tgt = db.session.query(Entry.content, Entry.lang).filter(Entry.id==tgt_id).first()
    src_tokenized , src_io = process(src.content, src.lang)
    tgt_tokenized , tgt_io = process(tgt.content, tgt.lang)
    hyp = db.session.query(Translation.translated).filter(Translation.parent_id==src_id)\
                    .first().translated
    if hyp:        
        hyp_io = StringIO(hyp)
        src_aligned, tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io)
    else:
        src_aligned, tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io=None)
    src_aligned = detok(src_aligned)
    tgt_aligned = detok(tgt_aligned)               
    src_entry = '\n'.join(src_aligned)
    tgt_entry = '\n'.join(tgt_aligned)
    return src_entry, tgt_entry




def paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, q_id, r_id):
    print('##########Article {} #########'.format(q_id),file=src_file)
    print(src_entry,file=src_file)
    print('##########Article {} #########'.format(r_id),file=tgt_file)
    print(tgt_entry,file=tgt_file)


def create_corpus(src_lang, tgt_lang, threshold):
    entries = db.session.query(Entry.id).filter(Entry.lang==src_lang).all()
    for entry in tqdm(entries):
        retrieved_id = get_match(entry.id, threshold)
        if retrieved_id:
            src_entry, tgt_entry = align_pairs(entry.id, retrieved_id)
            paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, entry.id, retrieved_id)


if __name__== '__main__':
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    parser.add_argument('threshold', type=float ,help='value of threshold')
    args = parser.parse_args()
    src_lang, tgt_lang, threshold = args.src_lang, args.tgt_lang, args.threshold
    src_file = open('./relaxed/pib_en-{}.{}.{}.txt'.format(src_lang, src_lang, threshold),'w+')
    tgt_file = open('./relaxed/pib_en-{}.{}.{}.txt'.format(src_lang, tgt_lang, threshold),'w+')
    create_corpus(src_lang, tgt_lang, threshold)