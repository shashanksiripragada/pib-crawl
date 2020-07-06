import os
import glob
from collections import defaultdict
from webapp.cli.utils import ParallelWriter 
from argparse import ArgumentParser

def remove(pib_dir, mkb_dir, iteration):
    reqs = ['hi', 'ml', 'ta', 'te', 'bn', 'mr', 'gu', 'or']
    for lang in reqs:
            mkb = defaultdict(list)
            pib = defaultdict(list)
            fpath = os.path.join(pib_dir,'pib-v{}'.format(iteration))
            fname = 'train'
            pwriter = ParallelWriter(fpath, fname)
            def dirname(xx):
                fst, snd = sorted([xx, 'en'])
                return '{}-{}'.format(fst, snd)

            dxx = dirname(lang)

            with open('{}/{}/mkb.{}'.format(mkb_dir, dxx, lang)) as src1,\
                 open('{}/{}/mkb.en'.format(mkb_dir, dxx, lang)) as tgt1,\
                 open('{}/{}/filtered.{}'.format(pib_dir, dxx, lang, lang)) as src2,\
                 open('{}/{}/filtered.en'.format(pib_dir, dxx, lang)) as tgt2:
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
                    pwriter.write(lang, 'en', k, pib[k][0])
                
if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--pib_dir', type=str, required=True)
    parser.add_argument('--mkb_dir', type=str, required=True)
    parser.add_argument('--iter', type=str, required=True)
    args = parser.parse_args()
    remove(args.pib_dir, args.mkb_dir, args.iter)