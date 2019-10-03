import time
import numpy as np
import langid
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from datetime import timedelta 
import datetime
from webapp import db
from webapp.models import Entry, Link, Translation
from sqlalchemy import func, and_
import itertools
from tqdm import tqdm
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
import os
from ilmulti.utils.language_utils import inject_token
import csv
from sklearn.metrics.pairwise import cosine_similarity
from collections import namedtuple
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import string
import re
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer

def preprocess(corpus):
    # takes in document content and returns processed document as string
    stop_words = set(stopwords.words('english'))
    ps = PorterStemmer()
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

def tfidf(query, candidates):
    vectorizer = TfidfVectorizer()
    candidate_features = vectorizer.fit_transform(candidates).toarray()
    query_feature = vectorizer.transform([query]).toarray()
    N, d = candidate_features.shape
    query_feature = np.tile(query_feature, (N, 1))
    similarities = cosine_similarity(query_feature, candidate_features)
    similarities = np.diag(similarities)
    indices = np.argsort(-1*similarities)
    return indices, similarities

def reorder(candidates, indices, similarities):
    Retrieved = namedtuple('Retrieved', 'id similarity')
    return [
        Retrieved(id=candidates[i], similarity=similarities[i]) \
        for i in indices
    ]

def get_candidates(query_id):
    langs = ['hi','ml','bn','te','ta','ur']
    delta = timedelta(days = 2)
    query = db.session.query(Entry)\
                .filter(Entry.id==query_id)\
                .first()                        
    candidates = []
    eng_matches = db.session.query(Entry.id) \
                    .filter(Entry.lang=='en') \
                    .filter(Entry.date.between(query.date-delta,query.date+delta))\
                    .all()

    noneng_matches = db.session.query(Entry) \
                    .filter(and_(Entry.lang!='en',Entry.lang.in_(langs))) \
                    .filter(Entry.date.between(query.date-delta,query.date+delta))\
                    .all()
    if query.lang == 'en':
        for match in noneng_matches:
            candidates.append((match.id,match.lang))  
        return candidates
    else:
        for match in eng_matches:
            candidates.append(match.id)   
        return candidates

def retrieve_neighbours_en(query_id):
    candidates = get_candidates(query_id)
    candidate_corpus = []
    query = Translation.query.filter(Translation.parent_id == query_id).first()
    query_content = preprocess(query.translated)        
    candidate_content = Entry.query.filter(Entry.id.in_(candidates)).all()
    for content in candidate_content:
        processed = preprocess(content.content)
        candidate_corpus.append(processed)

    indices, similarities = tfidf(query_content, candidate_corpus)
    export = reorder(candidates, indices, similarities)

    truncate_length = min(5, len(export))
    export = export[:truncate_length]
    return export


def retrieve_neighbours_nonen(query_id):
    candidates = get_candidates(query_id)
    candidate_ids = defaultdict(list)
    candidate_corpus = defaultdict(list)
    export = defaultdict(list)
    ids = [c[0] for c in candidates]
    candidate_langs = [c[1] for c in candidates]     
    query = Entry.query.filter(Entry.id == query_id).first()
    query_content = preprocess(query.content)     
    candidate_content = Translation.query\
                        .filter(Translation.parent_id.in_(ids))\
                        .all()
    for lang, content in zip(candidate_langs, candidate_content):
        processed = preprocess(content.translated)
        candidate_corpus[lang].append(processed)
        candidate_ids[lang].append(content.parent_id)
    for lang in candidate_corpus.keys():
        indices, similarities = tfidf(query_content, candidate_corpus[lang])
        export[lang] = reorder(candidate_ids[lang], indices, similarities)
      
    for lang in export:
        length = len(export[lang])
        truncate_length = min(5, length)
        export[lang] = export[lang][:truncate_length]
    return export   
    