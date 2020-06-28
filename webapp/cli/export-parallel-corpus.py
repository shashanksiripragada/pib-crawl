import os
import sys
import matplotlib.pyplot as plt
import numpy as np
from io import StringIO
from tqdm import tqdm
from argparse import ArgumentParser
from sqlalchemy import func, and_

from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all

from webapp import db
from webapp.models import Entry, Link, Translation, Retrieval

from bleualign.align import Aligner
from cli.utils import Preproc, ParallelWriter
from tools.align import BLEUAligner

#from urduhack.tokenization import sentence_tokenizer
from cli import ILMULTI_DIR

def get_datelinks(entry):
    links = []
    date_links = entry.neighbors
    for link in date_links:
        if link.second.lang == 'en':
            links.append(link.second_id)
    return list(set(links))

def get_src_hyp_io(src_id, tgt_lang, model):
    src_io, hyp_io = None, None
    exists = False
    entry = Entry.query.filter(
                Entry.id==src_id
            ).first()    
    hyp = Translation.query.filter(
                and_(
                    Translation.parent_id==src_id, 
                    Translation.model==model
                )
            ).first()

    if hyp and entry.content and hyp.translated:
        exists = True
        _, src_io = preproc.process(entry.content, entry.lang)
        hyp_io = StringIO(hyp.translated)
    return src_io, hyp_io, exists

def get_tgt_io(retrieved_id):
    tgt = Entry.query.filter(
            Entry.id==retrieved_id
        ).first()
    tgt_tokenized, tgt_io = preproc.process(tgt.content, tgt.lang)
    return tgt_io

def paralle_write(src_entry, src_lang, tgt_entry, tgt_lang, q_id, r_id):
    #print('##########Article {} #########'.format(q_id),file=src_file)
    print(src_entry,file=src_file)
    #print('##########Article {} #########'.format(r_id),file=tgt_file)
    print(tgt_entry,file=tgt_file)



def align(score, threshold, src_io, tgt_io, hyp_io, q, r): 
    src_aligned, tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io)
    src_aligned = preproc.detok(src_aligned)
    tgt_aligned = preproc.detok(tgt_aligned)               
    src_entry = '\n'.join(src_aligned)
    tgt_entry = '\n'.join(tgt_aligned)
    paralle_write(src_entry, src_lang, tgt_entry, \
                    tgt_lang, q, r)


def calculate_threshold(scores):
    mean = np.mean(scores)
    var = np.var(scores)
    std = np.std(scores)
    plt.hist(scores, bins=10)
    plt.ylabel('article counts');
    plt.savefig('./extraction/plots/{}_new.png'.format(src_lang))
    print(mean,var,std)
    return mean#std#mean+std


def export(src_lang, tgt_lang, model):
    entries = Entry.query.filter(
                Entry.lang==src_lang
                ).all()

    entry_list = [entry.id for entry in entries]
    retrieved = Retrieval.query.filter(
                    and_(
                    Retrieval.query_id.in_(entry_list), 
                    Retrieval.model==model
                    )
                ).all()
    scores = [r.score for r in retrieved if r]     
    threshold = calculate_threshold(scores)
    for entry in tqdm(entries):
        date_links = get_datelinks(entry)
        src_io, hyp_io, exists = get_src_hyp_io(entry.id, tgt_lang, model)
        if exists:            
            retrieved = Retrieval.query.filter(
                            and_(
                                Retrieval.query_id==entry.id, 
                                Retrieval.model==model
                            )
                        ).first()

            if retrieved:
                retrieved_id, score = retrieved.retrieved_id, retrieved.score
                tgt_io = get_tgt_io(retrieved_id)
                if retrieved_id in date_links:
                    align(
                        score, threshold, 
                        src_io, tgt_io, hyp_io, 
                        entry.id, retrieved_id
                    )
                elif score>=threshold:                    
                    align(
                        score, threshold, 
                        src_io, tgt_io, hyp_io, 
                        entry.id, retrieved_id
                    )

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    args = parser.parse_args()
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    #fpath = os.getcwd()
    #fname = 'pib_{}-{}'.format(tgt_lang, src_lang)
    #pwriter = ParallelWriter(fpath, fname)
    
    langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']

    segmenter = Segmenter()
    tokenizer = SentencePieceTokenizer()
    root = os.path.join(ILMULTI_DIR, 'mm-all')
    translator = mm_all(root=root, use_cuda=True).get_translator()
    aligner = BLEUAligner(translator, tokenizer, segmenter)
    preproc = Preproc(segmenter, tokenizer)


    model = 'mm_all_iter1'
    src_file = open('pib_{}_en-{}.{}.txt'.format(model, src_lang, src_lang),'a')
    tgt_file = open('pib_{}_en-{}.{}.txt'.format(model, src_lang, tgt_lang),'a')
    
    export(src_lang, tgt_lang, model)


