import random
import csv
from collections import defaultdict
import os
import pandas as pd
import numpy as np
from argparse import ArgumentParser
common = defaultdict(list)

random.seed(42)

def get_size(file):
    count = 0
    for line in file:
        count+=1
    return count

def get_fp(srcpath, tgtpath):
    srcfile = open(srcpath, 'r')
    tgtfile = open(tgtpath, 'r')
    return srcfile, tgtfile

def get_sample_pairs(src_lang, tgt_lang, srcpath, tgtpath, nsamples):
    srcfile, tgtfile = get_fp(srcpath, tgtpath)    
    srclines = get_size(srcfile)
    tgtlines = get_size(tgtfile)
    samples = random.sample(range(0,srclines), nsamples) 
    
    srclist, tgtlist = [], []
    srcfile, tgtfile = get_fp(srcpath, tgtpath)
    for index, (src, tgt) in enumerate(zip(srcfile, tgtfile)):
        if index in samples:
            src = src.strip()
            tgt = tgt.strip()
            srclist.append(src)
            tgtlist.append(tgt)
    pairs = list(set(zip(srclist, tgtlist)))
    pairs = pairs[:nsamples]
    srclist, tgtlist = list(zip(*pairs))

    return srclist, tgtlist


if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('--nsamples', help='', default=100, type=int, required=True)
    parser.add_argument('--src_lang', help='source language, non-english', required=True)
    parser.add_argument('--tgt_lang', help='target language', required=True )
    parser.add_argument('--model', help='translation model for generating dataset', required=True)
    args = parser.parse_args()
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    model, nsamples = args.model, args.nsamples

    fpath = './{}/{}-{}/'.format(model, src_lang, tgt_lang)
    srcpath = os.path.join(fpath, 'filtered.{}'.format(src_lang))
    tgtpath = os.path.join(fpath, 'filtered.{}'.format(tgt_lang))
  
    srclist, tgtlist = get_sample_pairs(src_lang, tgt_lang, srcpath, tgtpath, nsamples)

    df = pd.DataFrame()
    df['score'] = np.ones(len(srclist)).tolist()
    df['{}'.format(src_lang)] = srclist
    df['{}'.format(tgt_lang)] = tgtlist

    export_path = './{}/'.format(model)
    csvpath = os.path.join(export_path, '{}-{}.xlsx'.format(src_lang, tgt_lang))
    df.to_excel(csvpath, index=False)



 



            
            


