from collections import defaultdict
import matplotlib.pyplot as plt

from argparse import ArgumentParser
from sqlalchemy import and_, or_
from pprint import pprint

from ilmulti.translator import from_pretrained

from webapp.models import Entry, Link, Translation, Retrieval, Titles
from webapp.retrieval import *


def get_datelinks(entry, lang='en'):
    links = []
    date_links = entry.neighbors
    for link in date_links:
        if link.second.lang == lang:
            links.append(link.second_id)
    return list(set(links))

def check_pair_title(entry, link, lang):
    '''
        Title for some non-en articles (ex. hi, ml)
        can be in English. Below code takes care of that.
    '''
    arg = {'{}_title'.format(lang): entry.title}
    nonen_title = Titles.query.filter_by(**arg).first()

    nonen_title_en = Titles.query.filter(
                        Titles.en_title==entry.title
                    ).first()
    nonen_title = nonen_title or nonen_title_en
    
    en_title = Titles.query.filter(
                    Titles.en_title==link.title
                ).first()
    if nonen_title and en_title and nonen_title==en_title:
        return True
    else:
        return False

def check_pair_length(entry, link, diff=30):
    _, lang_segments = segmenter(entry.content, lang=entry.lang)
    _, en_segments = segmenter(link.content, lang=link.lang)
    lang_segments = list(filter(None, lang_segments))
    en_segments = list(filter(None, en_segments))
    length_diff = abs(len(lang_segments)-len(en_segments))                   
    if length_diff <= diff:
        return True
    else:
        return False

def check_retrieval(entry, link, model):
    retrieved = Retrieval.query.filter(
                    and_(
                        Retrieval.query_id==entry.id, 
                        Retrieval.model==model
                    )
                ).first()
    if retrieved:
        retrieved_id, score = retrieved.retrieved_id, retrieved.score
        if retrieved_id == link.id:
            return True
        else:
            return False

def calculate_threshold(lang, model):
    entries = Entry.query.filter(
                    Entry.lang==lang
              ).all()

    entry_ids = [entry.id for entry in entries]
    retrieved = Retrieval.query.filter(
                    and_(
                        Retrieval.query_id.in_(entry_ids), 
                        Retrieval.model==model
                    )
                ).all()
    scores = [r.score for r in retrieved if r]
    mean = np.mean(scores)
    var = np.var(scores)
    std = np.std(scores)
    plt.title('{} {}'.format(lang, model))
    plt.hist(scores, bins=10)
    plt.ylabel('{} article counts'.format(lang))
    plt.savefig('./plots/{}_{}.png'.format(lang, model))
    plt.close()
    print('mean: {} \n var: {} \n std: {} \n '.format(mean, var, std))

def sanity_check(lang, model):
    entries = Entry.query.filter(Entry.lang==lang).all()
    calculate_threshold(lang, model)
    articles = len(entries)
    date_match = 0
    title_match = 0
    content_length = 0
    retrieved = 0
    for entry in entries:
        date_links = get_datelinks(entry) 
        #for ix, link_id in enumerate(date_links):
        if date_links:
            link_id = date_links[0]
            date_match += 1
            link = Entry.query.filter(Entry.id==link_id).first()
            if check_pair_title(entry, link, lang):
                title_match += 1 
                # if check_pair_length(entry, link):
                #    content_length += 1
                if check_retrieval(entry, link, model):
                    retrieved += 1

    print('Total articles', articles)
    print('date_match', date_match)
    print('title_match', title_match)
    print('content_length', content_length)
    print('retrieved', retrieved, model, '\n')

if __name__ == '__main__':
    '''
        Sanity checks on a gold dataset determined
        by dates, title and content based matches.
    ''' 
    parser=ArgumentParser()
    parser.add_argument('lang', help='language for sanity checks')
    args = parser.parse_args()
    lang = args.lang

    engine = from_pretrained(tag='mm-to-en-iter1', use_cuda=False)
    segmenter = engine.segmenter
    #models = ['mm-all-iter1', 'mm-to-en-iter1', 'mm_all_iter0', 'mm-all-iter0', 'mm_toEN_iter1']:
    models = ['mm-all-iter1']

    for model in models:
        sanity_check(lang, model)