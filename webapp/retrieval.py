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
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import PorterStemmer
from .utils import clean_translation
from pprint import pprint


class SPMPreprocessor:
    def __init__(self, tokenizer, lang):
        self.tokenizer = tokenizer
        self.lang = lang

    def __call__(self, content):
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



def retrieve_neighbours_en(query_id, tokenizer, model='mm_toEN_iter1', length_check=True):
    candidates = get_candidates(query_id, days=2)
    query = (
        Translation.query.filter(
            and_(
                Translation.parent_id == query_id, 
                Translation.model==model
            )
        ).first()
    )

    preprocess = SPMPreprocessor(tokenizer, lang='en')

    query_content = preprocess(clean_translation(tokenizer, query))

    # Candidate content.
    # COMMENT(jerin): The following reorders stuff.
    candidate_content = Entry.query.filter(Entry.id.in_(candidates)).all()
    new_candidates = [ncc.id for ncc in candidate_content]

    candidate_corpus = []
    for content in candidate_content:
        processed = preprocess(content.content)
        candidate_corpus.append(processed)

    tf = RetrievalEngine(query_content, candidate_corpus, new_candidates)
    export = tf.reorder()

    truncate_length = min(5, len(export))
    export = export[:truncate_length]
    return export


def retrieve_neighbours_nonen(query_id):
    candidates = get_candidates(query_id, 2)
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
        similarities = tfidf(query_content, candidate_corpus[lang])
        export[lang] = reorder(candidate_ids[lang], similarities)
      
    for lang in export:
        length = len(export[lang])
        truncate_length = min(5, length)
        export[lang] = export[lang][:truncate_length]
    return export   
    
