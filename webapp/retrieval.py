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
        Retrieved(id=candidates[i].id, similarity=similarities[i]) \
        for i in indices
    ]

def get_candidates(query_id):
    delta = timedelta(days = 2)
    # entries = db.session.query(Translation.parent_id, Entry.date)\
    #                     .filter(Translation.parent_id == Entry.id)\
    #                     .order_by(Entry.date.desc())\
    #                     .first()
    #                     #.subquery()

    entry = db.session.query(Translation.parent_id, Entry.date)\
                        .filter(Translation.parent_id == Entry.id)\
                        .order_by(Entry.date.desc())\
                        .first()

    # for entry in tqdm(entries):
    #     posmatches[entry.parent_id] = []
    #     matches = db.session.query(Entry.id)\
    #                 .filter(Entry.lang=='en')\
    #                 .filter(Entry.date.between(entry.date-delta,entry.date+delta))\
    #                 .all()
    #     for match in matches:
    #         posmatches[entry.parent_id].append(match.id)   

    candidates = []
    matches = db.session.query(Entry.id) \
                .filter(Entry.lang=='en') \
                .filter(Entry.date.between(entry.date-delta,entry.date+delta))\
                .all()
    for match in matches:
        candidates.append(match.id)   
    return candidates

def retrieve_neighbours(query_id):
    candidates = get_candidates(query_id)
    corpus = []
    query_content = Translation.query.filter(Translation.parent_id == query_id).first()
    query = preprocess(query_content.translated)        
    content = Entry.query.filter(Entry.id.in_(candidates)).all()
    for _content in content:
        processed = preprocess(_content.content)
        corpus.append(processed)

    indices, similarities = tfidf(query, corpus)
    export = reorder(content, indices, similarities)

    truncate_length = min(5, len(export))
    export = export[:truncate_length]
    return export
