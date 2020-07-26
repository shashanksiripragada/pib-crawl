from collections import defaultdict
from itertools import combinations, permutations
import os
import pandas as pd
import langid
from argparse import ArgumentParser

class ParallelWriter:
    def __init__(self, fpath, fname):
        self.fpath = fpath
        self.fname = fname
        self.files = {}

    def get_fp(self, xx, yy):
        fst, snd = sorted([xx, yy])
        dirname = '{}-{}'.format(fst, snd)
        fpath = os.path.join(self.fpath, dirname)

        if not os.path.exists(fpath):
            os.makedirs(fpath)


        if (xx, yy) in self.files:
            return self.files[(xx, yy)]

        self.files[(xx, yy)] = [
            open(os.path.join(fpath, '{}.{}'.format(self.fname, xx)), 'w'),
            open(os.path.join(fpath, '{}.{}'.format(self.fname, yy)), 'w')
        ]

        return self.files[(xx, yy)]


    def write(self, src, tgt, srcline, tgtline):
        srcfile, tgtfile = self.get_fp(src, tgt)
        print(srcline, file=srcfile)
        print(tgtline, file=tgtfile)




def collect(xx, yy, input_dir, pwriter):
    common = defaultdict(list)
    def dirname(xx):
        fst, snd = sorted([xx, 'en'])
        return '{}-{}'.format(fst, snd)

    dxx = dirname(xx)
    dyy = dirname(yy)
    fname = 'train'
    with open('./{}/{}/{}.{}'.format(input_dir, dxx, fname, xx)) as src1,\
         open('./{}/{}/{}.en'.format(input_dir, dxx, fname)) as tgt1,\
         open('./{}/{}/{}.{}'.format(input_dir, dyy, fname, yy)) as src2,\
         open('./{}/{}/{}.en'.format(input_dir, dyy, fname)) as tgt2:
        
        for s1, t1 in zip(src1, tgt1):
            s1 = s1.strip()
            t1 = t1.strip()
            common[t1].append(s1)

        for s2, t2 in zip(src2, tgt2):
            s2 = s2.strip()
            t2 = t2.strip()
            common[t2].append(s2)


        for l in common:
            if len(common[l]) == 2:
                srcline, tgtline = common[l]
                src_pred , _ = langid.classify(srcline)
                tgt_pred , _ = langid.classify(tgtline)
                if (src_pred, tgt_pred) == (xx, yy):
                    pwriter.write(xx, yy, srcline, tgtline)

def get_stats(langs, fpath, fname):
    data = defaultdict(int)
    for lang in langs:
        data[lang] = 0

    df = pd.DataFrame(data, index = langs)
    perm = permutations(langs, 2)
    pairs = 0
    for direction in list(perm):
        direction = sorted(direction)
        xx, yy = direction

        try:
            src = open('{}/{}-{}/{}.{}'.format(fpath, xx, yy, fname, yy), 'r')
            pairs+=1
            count=0
            for line in src:
                count+=1
            src, tgt = direction
            a, b = langs.index(src), langs.index(tgt)

            if a>b:
                src, tgt = tgt, src
            df.at[src, tgt] = count

        except:
            #df.at[xx, yy] = 0
            pass            
    print(pairs)
    df.to_csv('grid_pib_v0.2.csv')

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('--input_dir', help='input directory containing xx-en',  required=True)
    parser.add_argument('--fpath', help='path to write multilingual data',  required=True)
    parser.add_argument('--fname', help='name to be written',  required=True)
    args = parser.parse_args()
    pwriter = ParallelWriter(args.fpath, args.fname)
    langs = ['en','hi','ta','te','ml','ur','bn','gu','mr','or','pa']
    perm = combinations(langs, 2)
    for xx, yy in list(perm):
        if  'en' not in [xx, yy]:
            print(xx, yy)
            collect(xx, yy, args.input_dir, pwriter)
    get_stats(langs, args.fpath, args.fname)


