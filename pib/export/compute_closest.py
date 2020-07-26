import os
import glob
from collections import defaultdict
from argparse import ArgumentParser
from pprint import pprint
from collections import namedtuple
from tqdm import tqdm
from webapp.cli.utils import ParallelWriter 
from fuzzywuzzy import fuzz
import editdistance
import Levenshtein as lev
import string

def dirname(xx):
    fst, snd = sorted([xx, 'en'])
    return '{}-{}'.format(fst, snd)

def distance(src, tgt):
    src, tgt = src.strip(), tgt.strip()

    src = src.translate(str.maketrans('', '', string.punctuation))
    tgt = tgt.translate(str.maketrans('', '', string.punctuation))

    src, tgt = src.lower(), tgt.lower()
    
    #dist = lev.distance(src, tgt)
    dist = editdistance.eval(src.split(), tgt.split())
    max_len = max(len(src.split()), len(tgt.split()))

    if max_len==0:
        max_len=1
    norm_dist = (max_len - dist) / max_len

    return norm_dist

def eval_len_ratio(src, tgt):    
    ratio = len(src.split())/len(tgt.split())
    if 0.7<=ratio<=1.5:
        return True
    else:
        return False


def closest(lang, pib_src, pib_tgt, mkb_list, src_len):
    
    fpath = './relaxed-modf'
    fname = 'common'
    pwriter = ParallelWriter(fpath, fname)
    threshold = 0.8
    
    for pib_idx, (spib, tpib) in enumerate(tqdm(zip(pib_src, pib_tgt), total=src_len)):
        spib, tpib = spib.rstrip(), tpib.rstrip()
        srcs, tgts = [], []

        for mkb_idx, (smkb, tmkb) in enumerate(mkb_list):            
            
            if eval_len_ratio(spib, smkb) or eval_len_ratio(tpib, tmkb):  
                src_edit = distance(spib, smkb)
                tgt_edit = distance(tpib, tmkb)
            else:
                src_edit = 0
                tgt_edit = 0
            
            srcs.append((mkb_idx, spib, smkb, src_edit))
            tgts.append((mkb_idx, tpib, tmkb, tgt_edit))
   
        srcs.sort(key=lambda x: x[3], reverse=True)
        tgts.sort(key=lambda x: x[3], reverse=True)

        src, tgt = srcs[:1], tgts[:1] #top 1 match
        (mkb_idx, pibs, smkb, src_dist) = src[0]
        (mkb_idx, pibt, tmkb, tgt_dist) = tgt[0]

        if src_dist>=threshold or tgt_dist>=threshold:
            pwriter.write(lang, 'en', (pib_idx, mkb_idx, pibs, smkb, src_dist),\
                                      (pib_idx, mkb_idx, pibt, tmkb, tgt_dist))

def main(pib_dir, mkb_dir, lang):

    #for lang in langs:
    dxx = dirname(lang)
    pdir = os.path.join(pib_dir, dxx)
    mdir = os.path.join(mkb_dir, dxx)

    mkb_src = open('{}/mkb.{}'.format(mdir, lang), 'r')
    mkb_tgt = open('{}/mkb.en'.format(mdir), 'r')
    pib_src = open('{}/train.{}'.format(pdir, lang), 'r')
    pib_tgt = open('{}/train.en'.format(pdir), 'r')

    mkb_list = []
    for smkb, tmkb in zip(mkb_src, mkb_tgt):
        smkb, tmkb = smkb.strip(), tmkb.strip()
        mkb_list.append((smkb, tmkb))
    
    def file_len(fname):
        for i, l in enumerate(fname):
            pass
        return i + 1
    src_len = file_len(pib_src)

    pib_src = open('{}/train.{}'.format(pdir, lang), 'r')
    closest(lang, pib_src, pib_tgt, mkb_list, src_len)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--pib_dir', required=True)
    parser.add_argument('--mkb_dir', required=True)
    parser.add_argument('--lang', required=True)
    args = parser.parse_args()
    main(args.pib_dir, args.mkb_dir, args.lang)