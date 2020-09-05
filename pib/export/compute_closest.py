import os
import string
from collections import defaultdict
from argparse import ArgumentParser
from pprint import pprint
from collections import namedtuple
from tqdm import tqdm
import editdistance
from ..cli.utils import ParallelWriter 

class TestDataStorage:
    def __init__(self, src_path, tgt_path):
        """
        Loads test-data into a structure and prepares to query
        compute_closest matches when a PIB sample is called.
        """
        self.test_data = []
        mkb_src = open(src_path, 'r')
        mkb_tgt = open(tgt_path, 'r')

        for src, tgt in zip(mkb_src, mkb_tgt):
            src, tgt = src.strip(), tgt.strip()
            self.test_data.append((src, tgt))

        mkb_src.close()
        mkb_tgt.close()

    def closest(self, src_line, tgt_line):
        srcs = []
        tgts = []
        for mkb_idx, (test_src, test_tgt) in enumerate(self.test_data):            
            if eval_len_ratio(spib, test_src) or eval_len_ratio(tpib, test_tgt):  
                src_edit = distance(src_line, test_src)
                tgt_edit = distance(tgt_line, test_tgt)
            else:
                src_edit = 0
                tgt_edit = 0
            srcs.append((mkb_idx, src_line, test_src, src_edit))
            tgts.append((mkb_idx, tgt_line, test_tgt, tgt_edit))
   
        srcs.sort(key=lambda x: x[3], reverse=True)
        tgts.sort(key=lambda x: x[3], reverse=True)

        (mkb_idx, pibs, smkb, src_dist) = srcs[0]
        (mkb_idx, pibt, tmkb, tgt_dist) = tgts[0]
        return srcs[0], tgts[0]


def dirname(src_lang, tgt_lang):
    fst, snd = sorted([src_lang, tgt_lang])
    return '{}-{}'.format(fst, snd)

def distance(src, tgt):
    def preproc(s):
        s = s.strip()
        s = s.translate(str.maketrans('', '', string.punctuation))
        s = s.lower()
        return s

    src = preproc(src)
    tgt = preproc(tgt)

    #dist = lev.distance(src, tgt)
    dist = editdistance.eval(src.split(), tgt.split())
    max_len = max(len(src.split()), len(tgt.split()))

    if max_len==0:
        max_len=1
    norm_dist = (max_len - dist) / max_len

    return norm_dist

def eval_len_ratio(src, tgt):    
    ratio = len(src.split())/len(tgt.split())
    if 0.9<=ratio<=1.1:
        return True
    else:
        return False

def main(args):
    dxx = dirname(args.src_lang, args.tgt_lang)
    # Load MannKiBaat into storage.
    mdir = os.path.join(args.mkb_dir, dxx)
    test_src_path = '{}/mkb.{}'.format(mdir, args.src_lang)
    test_tgt_path = '{}/mkb.{}'.format(mdir, args.tgt_lang)
    storage = TestDataStorage(test_src_path, test_tgt_path)

    # PIB initializations
    pdir = os.path.join(args.pib_dir, dxx)
    pib_src = open('{}/train.{}'.format(pdir, args.src_lang), 'r')
    pib_tgt = open('{}/train.{}'.format(pdir, args.tgt_lang), 'r')

    fname = 'train.minus.mkb'
    pwriter = ParallelWriter(pdir, fname)
    
    for pib_idx, (spib, tpib) in enumerate(tqdm(zip(pib_src, pib_tgt), total=src_len)):
        spib, tpib = spib.rstrip(), tpib.rstrip()
        src_mkb, tgt_mkb = storage.closest(spib, tpib)
        (mkb_idx, pibs, smkb, src_dist) = src_mkb
        (mkb_idx, pibt, tmkb, tgt_dist) = tgt_mkb

        if src_dist>=args.threshold or tgt_dist>=args.threshold:
            print(args.src_lang, args.tgt_lang, (pib_idx, mkb_idx, pibs, smkb, src_dist),\
                                      (pib_idx, mkb_idx, pibt, tmkb, tgt_dist))
        else:
            pwriter.write(args.src_lang, args.tgt_lang, spib, tpib)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--pib-dir', type=str, required=True)
    parser.add_argument('--mkb-dir', type=str, required=True)
    parser.add_argument('--src-lang', type=str, required=True)
    parser.add_argument('--tgt-lang', type=str,  default='en')
    parser.add_argument('--threshold', type=float, required=True)
    args = parser.parse_args()
    main(args)
