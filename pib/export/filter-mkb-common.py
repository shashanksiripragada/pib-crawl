import os
import glob
from collections import defaultdict
from ..cli.utils import ParallelWriter 
from argparse import ArgumentParser
from tqdm import tqdm

def remove(pib_dir, mkb_dir):
    reqs = ['hi', 'ml', 'ta', 'te', 'bn', 'mr', 'gu', 'or']
    for lang in reqs:
            mkb = defaultdict(list)
            pib = defaultdict(list)
            # fpath = os.path.join(pib_dir,'pib-v{}'.format(iteration))
            # fname = 'train'
            # pwriter = ParallelWriter(fpath, fname)
            def dirname(xx):
                fst, snd = sorted([xx, 'en'])
                return '{}-{}'.format(fst, snd)

            dxx = dirname(lang)

            with open('{}/{}/mkb.en'.format(mkb_dir, dxx, lang)) as src1,\
                 open('{}/{}/mkb.{}'.format(mkb_dir, dxx, lang)) as tgt1,\
                 open('{}/{}/train.en'.format(pib_dir, dxx, lang, lang)) as src2,\
                 open('{}/{}/train.{}'.format(pib_dir, dxx, lang)) as tgt2:
                for s1, t1 in zip(src1, tgt1):
                    s1 = s1.strip()
                    t1 = t1.strip()
                    mkb[s1].append(t1)
                smkb = set(mkb)
                for s2, t2 in zip(src2, tgt2):
                    s2 = s2.strip()
                    t2 = t2.strip()
                    pib[s2].append(t2)
                spib = set(pib)

                for k in spib.difference(smkb):
                    print(k, pib[k][0])
                    pwriter.write(lang, 'en', k, pib[k][0])

def dirname(xx):
    fst, snd = sorted([xx, 'en'])
    return '{}-{}'.format(fst, snd)

def clean(pib_dir, mkb_dir): #, common_dir):
    langs = ['hi', 'ml', 'ta', 'te', 'bn', 'mr', 'gu', 'or', 'ur']
    common_dir = 'relaxed-modf'
    
    fpath = 'pib-v0.2'
    fname = 'train'
    pibwriter = ParallelWriter(fpath, fname)
            
    for lang in langs:

        dxx = dirname(lang)
        common = os.path.join(common_dir, dxx)
        pdir = os.path.join(pib_dir, dxx)
        mdir = os.path.join(mkb_dir, dxx)
        comm_src = open('{}/common.{}'.format(common, lang), 'r')
        comm_tgt = open('{}/common.en'.format(common), 'r')
        pib_src = open('{}/train.{}'.format(pdir, lang), 'r')
        pib_tgt = open('{}/train.en'.format(pdir), 'r')
        mkb_src = open('{}/mkb.{}'.format(mdir, lang), 'r')
        mkb_tgt = open('{}/mkb.en'.format(mdir), 'r')

        pib_lines, mkb_lines = [], []
        for csrc, ctgt in zip(comm_src, comm_tgt):
            csrc = csrc.strip()
            pib_idx = int(csrc.strip('()').split(",")[0])
            mkb_idx = int(csrc.strip('()').split(",")[1])
            pib_lines.append(pib_idx)
            mkb_lines.append(mkb_idx)

        for i, (spib, tpib) in enumerate(zip(pib_src, pib_tgt)):
            spib, tpib = spib.strip(), tpib.strip()
            if i not in pib_lines:
                pibwriter.write(lang, 'en', spib, tpib)




if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--pib_dir', type=str, required=True)
    parser.add_argument('--mkb_dir', type=str, required=True)
    args = parser.parse_args()
    remove(args.pib_dir, args.mkb_dir)
    clean(args.pib_dir, args.mkb_dir)
