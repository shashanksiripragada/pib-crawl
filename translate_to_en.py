import time
import numpy as np
import langid
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from datetime import timedelta 
import datetime
from webapp import db
from webapp.models import Entry, Link, Translation, Retrieval
from sqlalchemy import func
import itertools
from tqdm import tqdm
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
import os
from ilmulti.utils.language_utils import inject_token
import csv
from sklearn.metrics.pairwise import cosine_similarity
from collections import namedtuple, defaultdict
from sqlalchemy import and_

segmenter = Segmenter()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
translator.cuda()
tokenizer = SentencePieceTokenizer()
#aligner = BLEUAligner(translator, tokenizer, segmenter)

def process(content,tgt_lang):
    lang, content = segmenter(content)
    output = []
    for line in content:
        if line:
            lang, _tokens = tokenizer(line)
            _out = ' '.join(_tokens)
            output.append(_out)        
    injected_toks = inject_token(output,tgt_lang)
  
    return injected_toks 

def detok(src_out):
    src = []
    for line in src_out:
        src_detok = tokenizer.detokenize(line)
        src.append(src_detok)
    return src   

langs = ['hi','ml','bn','te','ta','ur']
model = 'mm_all'
error = open('retrieval_error.txt','w+')

def translate():
    entries = db.session.query(Entry.id,Entry.lang,Entry.date,Entry.content)\
                .filter(Entry.lang.in_(langs)).all()
    tgt_lang = 'en'
    for entry in tqdm(entries):
        if entry.content:
            exists = Translation.query.filter(Translation.parent_id==entry.id).first()
            if not exists:
                src_tok = process(entry.content,tgt_lang=tgt_lang)
                out = translator(src_tok)
                hyps = [ gout['tgt'] for gout in out ]
                hyps = detok(hyps)
                translated = '\n'.join(hyps)
                entry = Translation(parent_id= entry.id, model= model, lang= tgt_lang, translated= translated)
                try:
                    db.session.add(entry)
                    db.session.commit()
                except:
                    print(entry.id,fp=error)

#translate()

from webapp.retrieval import get_candidates,reorder, preprocess, tfidf,retrieve_neighbours_en


def store_retrieved():
    queries = db.session.query(Translation)\
                        .all()

    for q in tqdm(queries):
        if q.translated:
            exists = Retrieval.query.filter(Retrieval.query_id==q.parent_id).first()
            if not exists:
                retrieved = retrieve_neighbours_en(q.parent_id) 
                retrieved_id = retrieved[0][0]
                score = retrieved[0][1]        
                entry = Retrieval(query_id=q.parent_id, retrieved_id=retrieved_id, score=score)
                try:
                    db.session.add(entry)
                    db.session.commit()
                except:
                    print(q.parent_id,fp=error)
store_retrieved()

langs = ['en', 'ml', 'ur', 'te', 'hi', 'pa', 'kn', 'or', 'as', 'gu', 'mr', 'ta', 'bn']

def get_sents():
    sents = dict.fromkeys(langs,0)
    matches = db.session.query(Entry) \
        .filter(Entry.lang.in_(langs)) \
        .all()
    for match in matches:
        if match.content:
            content_ = match.content.splitlines()
            count = sents[match.lang]
            count += len(content_)
            sents[match.lang] = count

    print(sents)
#get_sents()


