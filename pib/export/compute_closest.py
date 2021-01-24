import os
import string
from collections import defaultdict
from argparse import ArgumentParser
from pprint import pprint
from collections import namedtuple
from tqdm import tqdm
import editdistance
from ..cli.utils import ParallelWriter, file_line_count, canonical_lang_pair_dirname

class TestDataStorage:
    def __init__(self, path, src_lang, tgt_lang):
        """
        Loads test-data into a structure and prepares to query
        compute_closest matches when a PIB sample is called.
        """
        self.test_data = []
        mkb_src = open(os.path.join(path, 'mkb.{}'.format(src_lang)), 'r')
        mkb_tgt = open(os.path.join(path, 'mkb.{}'.format(tgt_lang)), 'r')

        for src, tgt in zip(mkb_src, mkb_tgt):
            src, tgt = src.strip(), tgt.strip()
            self.test_data.append((src, tgt))

        mkb_src.close()
        mkb_tgt.close()

    def closest(self, pib_src, pib_tgt):
        srcs = []
        tgts = []
        for mkb_idx, (test_src, test_tgt) in enumerate(self.test_data):            
            if eval_len_ratio(pib_src, test_src) or eval_len_ratio(pib_tgt, test_tgt):  
                src_edit = distance(pib_src, test_src)
                tgt_edit = distance(pib_tgt, test_tgt)
            else:
                src_edit = 0
                tgt_edit = 0
            srcs.append((mkb_idx, pib_src, test_src, src_edit))
            tgts.append((mkb_idx, pib_tgt, test_tgt, tgt_edit))
   
        srcs.sort(key=lambda x: x[3], reverse=True)
        tgts.sort(key=lambda x: x[3], reverse=True)

        (mkb_idx, pibs, smkb, src_dist) = srcs[0]
        (mkb_idx, pibt, tmkb, tgt_dist) = tgts[0]
        return srcs[0], tgts[0]

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
    dxx = canonical_lang_pair_dirname(args.src_lang, args.tgt_lang)
    # Load MannKiBaat into storage.
    mkb_dir = os.path.join(args.mkb_dir, dxx)
    storage = TestDataStorage(mkb_dir, args.src_lang, args.tgt_lang)

    # PIB initializations
    pib_dir = os.path.join(args.pib_dir, dxx) 
    fpath = os.path.join(pib_dir, 'train.{}'.format(args.src_lang))
    src_len = file_line_count(fpath)
    
    pib_src = open(os.path.join(pib_dir, 'train.{}'.format(args.src_lang)), 'r')
    pib_tgt = open(os.path.join(pib_dir, 'train.{}'.format(args.tgt_lang)), 'r')

    fname = 'train.minus.mkb'
    pwriter = ParallelWriter(pib_dir, fname)
    
    for pib_idx, (spib, tpib) in enumerate(tqdm(zip(pib_src, pib_tgt), total=src_len)):
        spib, tpib = spib.rstrip(), tpib.rstrip()
        src_mkb, tgt_mkb = storage.closest(spib, tpib)
        (mkb_idx, pibs, smkb, src_dist) = src_mkb
        (mkb_idx, pibt, tmkb, tgt_dist) = tgt_mkb

        if src_dist<args.threshold and tgt_dist<args.threshold:
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
