import sys
import numpy as np
sys.path.insert(1, '../')
from webapp import db
from io import StringIO
from webapp.models import Entry, Link, Translation, Retrieval
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
from utils import Preproc
from tools.align import BLEUAligner
from tqdm import tqdm
from argparse import ArgumentParser
from sqlalchemy import func, and_
from urduhack.tokenization import sentence_tokenizer
from cli import ILMULTI_DIR
langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = os.path.join(ILMULTI_DIR, 'mm-all')
translator = mm_all(root=root, use_cuda=True).get_translator()
aligner = BLEUAligner(translator, tokenizer, segmenter)
preproc = Preproc(segmenter, tokenizer)

def get_datelinks(entry):
    links = []
    date_links = entry.neighbors
    for link in date_links:
        if link.second.lang == 'en':
            links.append(link.second_id)
    return list(set(links))

def get_src_hyp_io(src_id, tgt_lang, model):
    entry = db.session.query(Entry.content, Entry.lang).filter(Entry.id==src_id).first()
    src_tok , src_io = preproc.process(entry.content, entry.lang)
    hyp = db.session.query(Translation).\
            filter(and_(Translation.parent_id==src_id, Translation.model==model)).\
            first().translated
    hyp_io = StringIO(hyp)
    return src_io, hyp, hyp_io

def get_tgt_io(retrieved_id):
    tgt = db.session.query(Entry.content, Entry.lang).filter(Entry.id==retrieved_id).first()
    tgt_tokenized , tgt_io = preproc.process(tgt.content, tgt.lang)
    return tgt_io


def paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, q_id, r_id):
    #print('##########Article {} #########'.format(q_id),file=src_file)
    print(src_entry,file=src_file)
    #print('##########Article {} #########'.format(r_id),file=tgt_file)
    print(tgt_entry,file=tgt_file)


def align(score, threshold, src_io, tgt_io, hyp_io, q, r): 
    src_aligned, tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io)
    src_aligned = preproc.detok(src_aligned)
    tgt_aligned = preproc.detok(tgt_aligned)               
    src_entry = '\n'.join(src_aligned)
    tgt_entry = '\n'.join(tgt_aligned)
    paralle_write(src_entry, src_lang, tgt_entry, \
                    tgt_lang, q, r)


def calculate_threshold(scores):
    mean = np.mean(scores)
    var = np.var(scores)
    std = np.std(scores)
    # plt.hist(scores, bins=10)
    # plt.ylabel('article counts');
    # plt.savefig('./plots/{}.png'.format(src_lang))
    return mean+1.5*std


def export(src_lang, tgt_lang, model):
    entries = db.session.query(Entry).filter(Entry.lang==src_lang).all()
    entry_list = [entry.id for entry in entries]
    retrieved = db.session.query(Retrieval)\
                     .filter(and_(Retrieval.query_id.in_(entry_list), Retrieval.model==model))\
                     .all()
    scores = [r.score for r in retrieved if r]     
    threshold = calculate_threshold(scores)
    for entry in tqdm(entries):
        src_io, hyp, hyp_io = get_src_hyp_io(entry.id, tgt_lang, model)
        retrieved = db.session.query(Retrieval)\
                            .filter(and_(Retrieval.query_id==entry.id, Retrieval.model==model))\
                            .first()

        date_links = get_datelinks(entry)
        if retrieved:
            retrieved_id, score = retrieved.retrieved_id, retrieved.score
            #if retrieved_id in date_links:
            if score>=threshold:       
                tgt_io = get_tgt_io(retrieved_id)
                align(score, threshold, src_io, tgt_io, hyp_io, entry.id, retrieved_id)


if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    args = parser.parse_args()
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    src_file = open('pib_en-{}.{}.txt'.format(src_lang, src_lang),'a')
    tgt_file = open('pib_en-{}.{}.txt'.format(src_lang, tgt_lang),'a')
    if src_lang in ['gu', 'mr', 'pa', 'or']:
        model = 'mm_all_iter0'
    else:
        model = 'mm_all'
    export(src_lang, tgt_lang, model)

