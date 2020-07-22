import os
import glob
from collections import defaultdict
from argparse import ArgumentParser
from pprint import pprint
from collections import namedtuple
import tqdm

from fuzzywuzzy import fuzz
import editdistance
import Levenshtein as lev


def dirname(xx):
    fst, snd = sorted([xx, 'en'])
    return '{}-{}'.format(fst, snd)

def distance(src, tgt):
    # dist = editdistance.eval(src, tgt)
    dist = lev.distance(src, tgt)
    return dist
    # ratio = fuzz.ratio(src, tgt)
    # partial_ratio = fuzz.partial_ratio(src, tgt)
    # token_sort_ratio = fuzz.token_sort_ratio(src, tgt)
    # token_set_ratio = fuzz.token_set_ratio(src, tgt)

    # return ratio, partial_ratio , token_sort_ratio, token_set_ratio

def compute(pib_src, pib_tgt, mkb_list):
    
    source = namedtuple('source', ('mkb', 'dist'))
    target = namedtuple('target', ('mkb', 'dist'))

    for spib, tpib in zip(pib_src, pib_tgt):
        spib = spib.rstrip()#.split()
        tpib = tpib.rstrip()#.split()
        srcs, tgts = [], []

        for smkb, tmkb in mkb_list:
            src_edit = distance(spib, smkb)
            tgt_edit = distance(tpib, tmkb)
            # src_ratio, psrc_ratio, src_sort_ratio, src_set_ratio = distance(spib, smkb)
            # tgt_ratio, ptgt_ratio, tgt_sort_ratio, tgt_set_ratio= distance(tpib.lower(), tmkb.lower())

            srcs.append(source(mkb=smkb, dist=src_edit))
            tgts.append(target(mkb=tmkb, dist=tgt_edit))

        srcs.sort(key=lambda x: x.dist) #, reverse=True)
        tgts.sort(key=lambda x: x.dist) #, reverse=True)
        src = srcs[:1]
        tgt = tgts[:1]
        if src[0].dist<=5 or tgt[0].dist<=5:
            print(spib, src, '\n')
            print(tpib, tgt, '\n')

def main():
    pib_dir = 'mm-to-en-iter2/pib-v2'
    mkb_dir = 'mkb'
    langs = ['hi', 'ml', 'ta', 'te', 'bn', 'mr', 'gu', 'or']
    for lang in langs:
        dxx = dirname(lang)
        pdir = os.path.join(pib_dir, dxx)
        mdir = os.path.join(mkb_dir, dxx)

        mkb_src = open('{}/mkb.{}'.format(mdir, lang), 'r')
        mkb_tgt = open('{}/mkb.en'.format(mdir), 'r')
        pib_src = open('{}/train.{}'.format(pdir, lang), 'r')
        pib_tgt = open('{}/train.en'.format(pdir), 'r')

        mkb_list = []
        for smkb, tmkb in zip(mkb_src, mkb_tgt):
            smkb = smkb.rstrip()#.split()
            tmkb = tmkb.rstrip()#.split()
            mkb_list.append((smkb, tmkb))
        
        compute(pib_src, pib_tgt, mkb_list)

main()