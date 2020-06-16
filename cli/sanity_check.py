import os
import sys
import numpy as np
sys.path.insert(1, os.getcwd())
sys.path.insert(1, '../')
from webapp import db
from io import StringIO
from collections import defaultdict
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

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = os.path.join(ILMULTI_DIR, 'mm-all')
translator = mm_all(root=root, use_cuda=True).get_translator()
aligner = BLEUAligner(translator, tokenizer, segmenter)
preproc = Preproc(segmenter, tokenizer)

def get_datelinks(entry, lang='en'):
    links = []
    date_links = entry.neighbors
    for link in date_links:
        if link.second.lang == lang:
            links.append(link.second_id)
    return list(set(links))

def check_pair_title(entry, link, lang):
    #query_title = '{}_title'.format(lang)
    nonen_title = Titles.query.filter(or_(Titles.ta_title==entry.title, 
                                          Titles.en_title==entry.title)).first()
    en_title = Titles.query.filter(Titles.en_title==link.title).first() 
    if nonen_title and en_title and nonen_title==en_title:        
        return True
    else:
        return False

def check_pair_length(entry, link, diff=20):
    _, lang_segments = segmenter(entry.content, lang=entry.lang)
    _, en_segments = segmenter(link.content, lang=link.lang)
    lang_segments = list(filter(None, lang_segments))
    en_segments = list(filter(None, en_segments))
    length_diff = abs(len(lang_segments)-len(en_segments))                   
    if length_diff <= diff:
        return True
    elif length_diff>=200:
        print(len(lang_segments), len(en_segments))
        print(entry.id, link.id, length_diff)
        return False

def check_retrieval(entry, link, model='mm_toEN_iter1'):
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
    retrieved = 0
    for entry in entries:
        date_links = get_datelinks(entry)
        if len(date_links) >= 1:
            date_match += 1 
        for ix, link_id in enumerate(date_links):
            link = Entry.query.filter(Entry.id==link_id).first()
            if check_pair_title(entry, link, lang):
                title_match += 1 
                #if check_pair_length(entry, link):
                #    content_length += 1
                if check_retrieval(entry, link, model):
                    retrieved += 1
    print('date_match', date_match)
    print('title_match', title_match)
    #print('content_length', content_length)
    print('retrieved', retrieved, model)

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('lang', help='language of the content')
    parser.add_argument('model', help='model to perform sanity checks')
    args = parser.parse_args()
    model, lang = args.model, args.lang
    sanity_check(lang, model)