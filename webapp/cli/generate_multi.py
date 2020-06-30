from collections import defaultdict
from itertools import combinations, permutations
import os
import pandas as pd
import langid
from argparse import ArgumentParser
#from ilmulti.sentencepiece import SentencePieceTokenizer


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
    # with open('./{}/{}/mkb-filt.{}'.format(input_dir, dxx, xx)) as src1,\
    #      open('./{}/{}/mkb-filt.en'.format(input_dir, dxx)) as tgt1,\
    #      open('./{}/{}/mkb-filt.{}'.format(input_dir, dyy, yy)) as src2,\
    #      open('./{}/{}/mkb-filt.en'.format(input_dir, dyy)) as tgt2:
    with open('./{}/{}/train.{}'.format(input_dir, dxx, xx)) as src1,\
         open('./{}/{}/train.en'.format(input_dir, dxx)) as tgt1,\
         open('./{}/{}/train.{}'.format(input_dir, dyy, yy)) as src2,\
         open('./{}/{}/train.en'.format(input_dir, dyy)) as tgt2:
        
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

    for i in list(perm):
        try:
            src = open('{}/{}-{}/{}.{}'.format(fpath,i[0], i[1], fname,i[1]), 'r')
            #tgt = open('./extract/{}-{}/mkb.{}'.format(i[0], i[1], i[1]), 'r')
            count=0
            for line in src:
                count+=1
            src, tgt = i
            a, b = langs.index(src), langs.index(tgt)

            if a>b:
                src, tgt = tgt, src
            df.at[src, tgt] = count

        except:
            #df.at[i[0],i[1]] = 0
            pass            

    df.to_csv('grid_pib_filt.csv')

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('--input_dir', help='input directory containing xx-en',  required=True)
    parser.add_argument('--fpath', help='path to write multilingual data',  required=True)
    parser.add_argument('--fname', help='name to be written',  required=True)
    args = parser.parse_args()
    #fpath = './mkb-filt/'
    #fname = 'mkb-filt'
    pwriter = ParallelWriter(args.fpath, args.fname)
    langs = ['en', 'hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'or', 'pa']
    #langs = sorted(langs)
    perm = combinations(langs, 2)
    # for xx, yy in list(perm):
    #     if  'en' not in [xx, yy]:
    #         print(xx, yy)
    #         collect(xx, yy, args.input_dir, pwriter)
    get_stats(langs, args.fpath, args.fname)


