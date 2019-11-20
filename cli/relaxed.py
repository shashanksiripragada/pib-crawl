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
from webapp.retrieval import get_candidates, retrieve_neighbours_en

def get_match(src_id, threshold):
    thresh=threshold
    retrieved = db.session.query(Retrieval).filter(Retrieval.query_id==src_id)\
                          .first()
    link = db.session.query(Link).filter(Link.first_id==src_id).distinct().all()

    if retrieved and (link==[]):
        if retrieved.score >= thresh:
            return retrieved.retrieved_id

def align_pairs(src_id, tgt_id, model):
    # assuming src is non-en 
    src = db.session.query(Entry.content, Entry.lang).filter(Entry.id==src_id).first()
    tgt = db.session.query(Entry.content, Entry.lang).filter(Entry.id==tgt_id).first()
    src_tokenized , src_io = process(src.content, src.lang)
    tgt_tokenized , tgt_io = process(tgt.content, tgt.lang)
    hyp = db.session.query(Translation.translated)\
                    .filter(and_(Translation.parent_id==src_id,Translation.model==model))\
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


def create_corpus(src_lang, tgt_lang, model, threshold):
    entries = db.session.query(Entry.id).filter(Entry.lang==src_lang).all()
    for entry in tqdm(entries):
        retrieved_id = get_match(entry.id, threshold)
        if retrieved_id:
            src_entry, tgt_entry = align_pairs(entry.id, retrieved_id, model)
            paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, entry.id, retrieved_id)


if __name__== '__main__':
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    parser.add_argument('threshold', type=float ,help='value of threshold')
    args = parser.parse_args()
    model = 'mm_all_iter0'
    src_lang, tgt_lang, threshold = args.src_lang, args.tgt_lang, args.threshold
    src_file = open('./relaxed/pib_en-{}.{}.{}.txt'.format(src_lang, src_lang, threshold),'w+')
    tgt_file = open('./relaxed/pib_en-{}.{}.{}.txt'.format(src_lang, tgt_lang, threshold),'w+')
    create_corpus(src_lang, tgt_lang, model, threshold)
