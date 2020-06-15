import os
import sys
import numpy as np
sys.path.insert(1, os.getcwd())
sys.path.insert(1, '../')
from webapp import db
from io import StringIO
import matplotlib.pyplot as plt
from webapp.models import Entry, Link, Translation, Retrieval, Titles
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
from cli.utils import Preproc, ParallelWriter
from tools.align import BLEUAligner
from tqdm import tqdm
from argparse import ArgumentParser
from sqlalchemy import func, and_, or_
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

def check_pair_title(entry, link):
    nonen_title = Titles.query.filter(or_(Titles.nonen_title==entry.title, 
                                          Titles.en_title==entry.title)).first()
    en_title = Titles.query.filter(Titles.en_title==link.title).first() 
    if nonen_title and en_title and nonen_title==en_title:
        return True
    else:
        return False

def check_pair_length(entry, link, diff=10):
    _, hi_segments = segmenter(entry.content, lang=entry.lang)
    _, en_segments = segmenter(link.content, lang=link.lang)                
    if abs(len(hi_segments)-len(en_segments))<=diff:
        return True
    else:
        return False

def check_retrieval(entry, link, model='mm_all_iter0'):
    retrieved = db.session.query(Retrieval)\
                .filter(and_(Retrieval.query_id==entry.id, Retrieval.model==model))\
                .first()
    if retrieved:
        retrieved_id, score = retrieved.retrieved_id, retrieved.score
        if retrieved_id == link.id:
            return True
        else:
            return False

def sanity_check(lang, model):
    entries = Entry.query.filter(Entry.lang==lang).all()
    date_match = 0
    title_match = 0
    content_length = 0
    for entry in entries:
        date_links = get_datelinks(entry)
        for link_id in date_links:
            date_match += 1
            link = Entry.query.filter(Entry.id==link_id).first()
            if check_pair_title(entry, link):
                title_match+=1 
                if check_pair_length(entry, link):
                    content_length += 1
                    #and check_retrieval(entry, link, model):
                    
    print('date_match', date_match, 'title_match', title_match)
    print('content_length', content_length)
                    

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('lang', help='language of the content')
    parser.add_argument('model', help='model to perform sanity checks')
    args = parser.parse_args()
    model, lang = args.model, args.lang
    sanity_check(lang, model)


