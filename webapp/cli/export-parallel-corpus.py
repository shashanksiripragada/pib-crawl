import os
import numpy as np
import logging
from io import StringIO
from tqdm import tqdm
from collections import defaultdict
from argparse import ArgumentParser
from sqlalchemy import func, and_, or_

from ilmulti.translator import from_pretrained

from .. import db
from ..models import Entry, Link, Translation, Retrieval
from .utils import Preproc, ParallelWriter

from tools.align import BLEUAligner

def get_datelinks(entry, lang='en'):
    links = []
    date_links = entry.neighbors
    for link in date_links:
        if link.second.lang == lang:
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

def align(src_io, tgt_io, hyp_io, 
            query_id, retrieved_id, 
            src_lang, tgt_lang): 
    src_aligned, tgt_aligned = aligner.bleu_align(src_io, tgt_io, hyp_io)
    src_aligned = preproc.detok(src_aligned)
    tgt_aligned = preproc.detok(tgt_aligned)               
    src_entry = '\n'.join(src_aligned)
    tgt_entry = '\n'.join(tgt_aligned)
    pwriter.write(src_lang, tgt_lang, src_entry, tgt_entry)
    print('{} {}'.format(query_id, retrieved_id), file=aligned)

def calculate_threshold(scores):
    mean = np.mean(scores)
    var = np.var(scores)
    std = np.std(scores)
    threshold = mean-std
    return threshold

def aligned_entries(model, src_lang, tgt_lang):
    aligned = '{}-aligned-{}-{}.txt'.format(model, src_lang, tgt_lang)
    aligned_dict = defaultdict(int)
    if os.path.exists(aligned):
        file = open(aligned, 'r')
        for line in file:
            src_id, tgt_id = line.split()
            src_id, tgt_id = int(src_id), int(tgt_id)
            aligned_dict[src_id] = tgt_id
        return aligned_dict
    else:
        return False

def export(src_lang, tgt_lang, model, resume_from=0):
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
    aligned_dict = aligned_entries(model, src_lang, tgt_lang)
    counter = 0

    for entry in tqdm(entries):
        if counter < resume_from:
            counter += 1
            continue;
        counter += 1
        # date_links = get_datelinks(entry)        
        is_aligned = entry.id in aligned_dict
        src_io, hyp_io, exists = get_src_hyp_io(entry.id, tgt_lang, model)
        if exists and not is_aligned:            
            retrieved = Retrieval.query.filter(
                            and_(
                                Retrieval.query_id==entry.id, 
                                Retrieval.model==model
                            )
                        ).first()
            if retrieved:
                retrieved_id, score = retrieved.retrieved_id, retrieved.score
                tgt_io = get_tgt_io(retrieved_id)
                # if retrieved_id in date_links:
                #     align( 
                #         src_io, tgt_io, hyp_io, 
                #         entry.id, retrieved_id
                #     )
                if score >= threshold:                    
                    align(
                        src_io, tgt_io, hyp_io, 
                        entry.id, retrieved_id,
                        src_lang, tgt_lang
                    )

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('--src_lang', help='source language, non-english', required=True)
    parser.add_argument('--tgt_lang', help='target language', required=True )
    parser.add_argument('--model', help='translation model for generating dataset', required=True)
    parser.add_argument('--resume-from', help='', default=0, type=int)
    args = parser.parse_args()

    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    model = args.model

    # LOG_FILENAME = '{}.log'.format(model)
    # logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
    # logging.debug('{}'.format(model))

    engine = from_pretrained(tag=model, use_cuda=False)
    aligner = BLEUAligner(engine.translator, engine.tokenizer, engine.segmenter)
    preproc = Preproc(engine.segmenter, engine.tokenizer)
    
    fpath = '{}'.format(model)    
    pwriter = ParallelWriter(fpath, fname='aligned')
    aligned = open('{}-aligned-{}-{}.txt'.format(model, src_lang, tgt_lang), 'a')
    export(src_lang, tgt_lang, model, args.resume_from)