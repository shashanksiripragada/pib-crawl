from datetime import timedelta 
import datetime
from . import db
from .models import Entry, Link, Translation
from sqlalchemy import func, and_
import itertools
from tqdm import tqdm
from collections import namedtuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import string
import re
from .utils import clean_translation
from pprint import pprint


class SPMPreprocessor:
    def __init__(self, tokenizer, lang):
        self.tokenizer = tokenizer
        self.lang = lang

    def __call__(self, content):
        # print(content, type(content))
        _, content = self.tokenizer(content, lang=self.lang)
        return ' '.join(content)


class RetrievalEngine:
    def __init__(self, query, candidates, candidate_idxs):
        self.query = query
        self.candidates = candidates
        self.candidate_idxs = candidate_idxs
        self.compute_features()

    def compute_features(self):
        query = self.query
        candidates = self.candidates

        self.vectorizer = TfidfVectorizer()

        # Fits and transforms on existing data.
        self.candidate_features = self.vectorizer.fit_transform(candidates).toarray()
        self.query_feature = self.vectorizer.transform([query]).toarray()

        # Compute similarities.
        N, d = self.candidate_features.shape

        def batch_cosine_similarity(query_feature, candidate_features):
            query_feature = np.tile(query_feature, (N, 1))
            cs = cosine_similarity(query_feature, candidate_features)
            cs = np.diag(cs)
            return cs

        bcs = batch_cosine_similarity(self.query_feature, self.candidate_features)
        self.similarities = bcs


    def reorder(self):
        candidate_idxs = self.candidate_idxs
        Retrieved = namedtuple('Retrieved', 'id similarity')
        sorted_indices = np.argsort(-1*self.similarities)
        return [
            Retrieved(id=candidate_idxs[idx], similarity=self.similarities[idx])
            for idx in sorted_indices
        ]


def get_candidates(query_id, days):
    langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']
    delta = timedelta(days = days)
    query = (
        db.session.query(Entry)
            .filter(Entry.id==query_id)
            .first()
    )

    candidates = []

    if query.lang == 'en':
        noneng_matches = db.session.query(Entry) \
                        .filter(and_(Entry.lang!='en',Entry.lang.in_(langs))) \
                        .filter(Entry.date.between(query.date-delta,query.date+delta))\
                        .all()
        for match in noneng_matches:
            candidates.append((match.id,match.lang))  
        return candidates
    else:
        eng_matches = (
            db.session.query(Entry.id) 
                .filter(Entry.lang=='en')
                .filter(Entry.date.between(query.date-delta,query.date+delta))
                .all()
        )

        for match in eng_matches:
            candidates.append(match.id)   
        return candidates


def get_candidates_by_lang(query_id, lang, days):
    delta = timedelta(days = days)
    query = (
        db.session.query(Entry)
            .filter(Entry.id==query_id)
            .first()
    )
    candidates = []
    matches = (
        db.session.query(Entry.id) 
            .filter(Entry.lang==lang)
            .filter(Entry.date.between(query.date-delta,query.date+delta))
            .all()
    )
    for match in matches:
        candidates.append(match.id)   
    return candidates


def retrieve_neighbours(
        query_id, pivot_lang, tokenizer, 
        model, length_check=True):

    candidates = get_candidates_by_lang(query_id, pivot_lang, days=2)
    query = (
        Translation.query.filter(
            and_(
                Translation.parent_id == query_id, 
                Translation.model == model,
                Translation.lang == pivot_lang
            )
        ).first()
    )

    # Where to find neighbours if empty.
    if query is None:
        return []

    preprocess = SPMPreprocessor(tokenizer, lang=pivot_lang)
    query_content = preprocess(clean_translation(tokenizer, query))

    candidate_content = Entry.query.filter(Entry.id.in_(candidates)).all()
    new_candidates = [ncc.id for ncc in candidate_content]

    candidate_corpus = []
    for content in candidate_content:
        if content.content is None:
            print(content, content.content, content.id)
        content.content = content.content or ''
        processed = preprocess(content.content)
        candidate_corpus.append(processed)

    if candidate_corpus:
        tf = RetrievalEngine(query_content, candidate_corpus, new_candidates)
        export = tf.reorder()
        truncate_length = min(5, len(export))
        export = export[:truncate_length]
    else:
        export = []
    return export
