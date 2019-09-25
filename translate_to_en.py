import time
import numpy as np
import langid
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from datetime import timedelta 
import datetime
from webapp import db
from webapp.models import Entry, Link, Translation
from sqlalchemy import func
import itertools
from tqdm import tqdm
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
import os
from ilmulti.utils.language_utils import inject_token
import csv


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
error = open('translate_error.txt','w+')
'''
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
'''
#posmatches = {}
def retrieve():
    delta = timedelta(days = 2)

    entries = db.session.query(Translation.parent_id, Entry.date)\
                        .filter(Translation.parent_id == Entry.id)\
                        .order_by(Entry.date.desc())\
                        .first()
                        #.subquery()

    for entry in tqdm(entries):
        posmatches[entry.parent_id] = []
        matches = db.session.query(Entry.id)\
                    .filter(Entry.lang=='en')\
                    .filter(Entry.date.between(entry.date-delta,entry.date+delta))\
                    .all()
        for match in matches:
            posmatches[entry.parent_id].append(match.id)   
    
#retrieve()
'''
with open('posmatches.csv', 'w') as csv_file:
    writer = csv.writer(csv_file)
    for key, value in posmatches.items():
       writer.writerow([key, value])

'''
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import string
import re
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
stop_words = set(stopwords.words('english'))
ps = PorterStemmer()

def preprocess(corpus):
    processed = []
    corpus = corpus.splitlines()
    #corpus = sent_tokenize(corpus)
    for corp in corpus:
        translator = str.maketrans('','',string.punctuation)
        corp = corp.translate(translator)
        tokens = word_tokenize(corp)
        no_stop = [ps.stem(w.lower()) for w in tokens if not w in stop_words]
        alpha = [re.sub(r'\W+', '', a) for a in no_stop]
        alpha = [a for a in alpha if a]
        for a in alpha:
            processed.append(a)

    return ' '.join(processed)

with open('posmatches.csv', 'r') as f:
    data = csv.reader(f)
    corpus = []
    for row in data:
        query_id = row[0]
        posmatches = row[1]
        posmatches = posmatches[1:-1].split(',')
        posmatches = [pos.strip(' ') for pos in posmatches]
        posmatches = [int(i) for i in posmatches]
        query_content = Translation.query.filter(Translation.parent_id == query_id).first()
        query = preprocess(query_content.translated)        
        content = Entry.query.filter(Entry.id.in_(posmatches)).all()
        for _content in content:
            processed = preprocess(_content.content)
            corpus.append(processed)
        
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(corpus)
        q = vectorizer.transform([query])
        print(q)
        


        





