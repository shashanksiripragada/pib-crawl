import sys
sys.path.insert(1, '../')
from webapp import db
from io import StringIO
from webapp.models import Entry, Link, Translation, Retrieval
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
from utils import detok, process, create_stringio
from tools.align import BLEUAligner
from tqdm import tqdm
from argparse import ArgumentParser
from sqlalchemy import func, and_
from webapp.retrieval import get_candidates, retrieve_neighbours_en

segmenter = Segmenter()
tokenizer = SentencePieceTokenizer()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root, use_cuda=True).get_translator()
aligner = BLEUAligner(translator, tokenizer, segmenter)


def datelinks(entry):
    links = []
    date_links = entry.neighbors
    for link in date_links:
        if link.second.lang == 'en':
            links.append(link.second_id)
    return list(set(links))

def get_tgt(retrieved_id):
    tgt = db.session.query(Entry.content, Entry.lang).filter(Entry.id==retrieved_id).first()
    tgt_tokenized , tgt_io = process(tgt.content, tgt.lang)
    return tgt_io

def calculate_threshold(scores):
    mean = np.mean(scores)
    var = np.var(scores)
    std = np.std(scores)
    plt.hist(scores, bins=10)
    plt.ylabel('article counts');
    plt.savefig('./plots/{}.png'.format(src_lang))
    return mean - std

def get_match(src_id, threshold):
    thresh=threshold
    retrieved = db.session.query(Retrieval).filter(Retrieval.query_id==src_id)\
                          .first()
    link = db.session.query(Link).filter(Link.first_id==src_id).distinct().all()

    if retrieved and (link==[]):
        if retrieved.score >= thresh:
            return retrieved.retrieved_id

def align_pairs(src_id, tgt_id, model):
    # assuming src is non-en 
    src = db.session.query(Entry.content, Entry.lang).filter(Entry.id==src_id).first()
    tgt = db.session.query(Entry.content, Entry.lang).filter(Entry.id==tgt_id).first()
    src_tokenized , src_io = process(src.content, src.lang)
    tgt_tokenized , tgt_io = process(tgt.content, tgt.lang)
    hyp = db.session.query(Translation.translated)\
                    .filter(and_(Translation.parent_id==src_id,Translation.model==model))\
                    .first().translated
    if hyp:        
        hyp_io = StringIO(hyp)
        src_aligned, tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io)
    else:
        src_aligned, tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io=None)
    src_aligned = detok(src_aligned)
    tgt_aligned = detok(tgt_aligned)               
    src_entry = '\n'.join(src_aligned)
    tgt_entry = '\n'.join(tgt_aligned)
    return src_entry, tgt_entry


def paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, q_id, r_id):
    print(src_entry,file=src_file)
    print(tgt_entry,file=tgt_file)


def create_corpus(src_lang, tgt_lang, model, threshold):
    entries = db.session.query(Entry.id).filter(Entry.lang==src_lang).all()
    for entry in tqdm(entries):
        retrieved_id = get_match(entry.id, threshold)
        if retrieved_id:
            src_entry, tgt_entry = align_pairs(entry.id, retrieved_id, model)
            paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, entry.id, retrieved_id)


if __name__== '__main__':
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    #parser.add_argument('threshold', type=float ,help='value of threshold')
    args = parser.parse_args()
    if src_lang in ['gu', 'mr', 'pa', 'or']:
        model = 'mm_all_iter0'
    else:
        model = 'mm_all'
    #src_lang, tgt_lang, threshold = args.src_lang, args.tgt_lang, args.threshold
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    src_file = open('./relaxed/pib_en-{}.{}.txt'.format(src_lang, src_lang),'a')
    tgt_file = open('./relaxed/pib_en-{}.{}.txt'.format(src_lang, tgt_lang),'a')
    create_corpus(src_lang, tgt_lang, model)

 





def get_src_hyp(src_id, tgt_lang, model):
    entry = db.session.query(Entry.content, Entry.lang).filter(Entry.id==src_id).first()
    src_tok , src_io = process(entry.content, entry.lang)
    hyp = db.session.query(Translation).\
            filter(and_(Translation.parent_id==src_id, Translation.model==model)).\
            first().translated
    hyp_io = StringIO(hyp)
    return src_io, hyp, hyp_io

def align(score, threshold, src_io, tgt_io, hyp_io, q, r):
    if score >= threshold:  
        src_aligned, tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io)
        src_aligned = detok(src_aligned)
        tgt_aligned = detok(tgt_aligned)               
        src_entry = '\n'.join(src_aligned)
        tgt_entry = '\n'.join(tgt_aligned)
        paralle_write(src_entry, src_lang, tgt_entry, \
                        tgt_lang, q, r)





def create_corpus(src_lang, tgt_lang, model):
    scores = []
    entries = db.session.query(Entry).filter(Entry.lang==src_lang).all()
    for entry in tqdm(entries):
        retrieved = db.session.query(Retrieval)\
                      .filter(and_(Retrieval.query_id==entry.id, Retrieval.model==model))\
                      .first()
        if retrieved:
            retrieved_id, score = retrieved.retrieved_id, retrieved.score
            scores.append(score)
    threshold = calculate_threshold(scores)
    for entry in tqdm(entries):
        retrieved = db.session.query(Retrieval)\
                      .filter(and_(Retrieval.query_id==entry.id, Retrieval.model==model))\
                      .first()
        if retrieved:
            retrieved_id, score = retrieved.retrieved_id, retrieved.score
        date_links = datelinks(entry)
        src_io, hyp, hyp_io = get_src_hyp(entry.id, tgt_lang, model)
        tgt_io = get_tgt(retrieved_id)
        align(score, threshold, src_io, tgt_io, hyp_io, entry.id, retrieved_id)
  

if __name__== '__main__':
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    #parser.add_argument('threshold', type=float ,help='value of threshold')
    args = parser.parse_args()
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    #src_lang, tgt_lang, threshold = args.src_lang, args.tgt_lang, args.threshold
    if src_lang in ['gu', 'mr', 'pa', 'or']:
        model = 'mm_all_iter0'
    else:
        model = 'mm_all'
    
    src_file = open('./new_langs/minus_sigma/pib_en-{}.{}.txt'.format(src_lang, src_lang),'a')
    tgt_file = open('./new_langs/minus_sigma/pib_en-{}.{}.txt'.format(src_lang, tgt_lang),'a')
    create_corpus(src_lang, tgt_lang, model)



''' 
    if retrieved_id in date_links: # if date link and ret links match   
    num_links = 0
    num_matches = 0
    if date_links:
        num_links+=1
        if retrieved_id in date_links:
            num_matches+=1
print(num_links, num_matches)
'''