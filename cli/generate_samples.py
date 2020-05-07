import random
import csv
from collections import defaultdict
import os
import pandas as pd
import numpy as np
from argparse import ArgumentParser
common = defaultdict(list)

random.seed(42)

class ParallelWriter:
    def __init__(self, fpath):
        self.fpath = fpath
        self.files = {}

    def get_fp(self, xx, yy):

        if not os.path.exists(fpath):
            os.makedirs(fpath)


        if (xx, yy) in self.files:
            return self.files[(xx, yy)]

        self.files[(xx, yy)] = [
            open(os.path.join(fpath, '{}.{}'.format('pib-sampled', xx)), 'w'),
            open(os.path.join(fpath, '{}.{}'.format('pib-sampled', yy)), 'w')
        ]

        return self.files[(xx, yy)]

    def write(self, src, tgt, srcline, tgtline):
        srcfile, tgtfile = self.get_fp(src, tgt)
        print(srcline, file=srcfile)
        print(tgtline, file=tgtfile)


def get_size(file):
    count = 0
    for line in file:
        count+=1
    return count

def get_random_lines(start, end, num):
    lines = []
    return 
    return lines 

def get_samples(xx, yy, srcfile, tgtfile, samples):
    srclist = []
    tgtlist = []
    for index, (src, tgt) in enumerate(zip(srcfile, tgtfile)):
        if index in samples:
            src = src.strip()
            tgt = tgt.strip()
            srclist.append(src)
            tgtlist.append(tgt)

    return srclist, tgtlist
            #pwriter.write(xx, yy, src, tgt)


def get_fp(srcpath, tgtpath):
    srcfile = open(srcpath, 'r')
    tgtfile = open(tgtpath, 'r')
    return srcfile, tgtfile

if __name__ == '__main__':
    #langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']
    
    #langs = ['ta']
    parser=ArgumentParser()
    parser.add_argument('src_lang', help='non-english language')
    args = parser.parse_args()
    lang = args.src_lang

    #for lang in src_lang:
    try:
        df = pd.DataFrame()
        fpath = './'#.format(lang)
        srcpath = os.path.join(fpath, '{}.{}-{}.{}'.format('train', 'en', lang, 'en'))
        tgtpath = os.path.join(fpath, '{}.{}-{}.{}'.format('train', 'en', lang, lang))

        srcfile, tgtfile = get_fp(srcpath, tgtpath)    
        srclines = get_size(srcfile)
        tgtlines = get_size(tgtfile)
        samples = random.sample(range(0,srclines), 100)
        
        #pwriter = ParallelWriter(fpath)
        srcfile, tgtfile = get_fp(srcpath, tgtpath)   
        srclist, tgtlist = get_samples('en', lang, srcfile, tgtfile, samples)

        pairs = list(set(zip(srclist, tgtlist)))

        pairs = pairs[:100]
        srclist, tgtlist = list(zip(*pairs))

        df['score'] = np.ones(len(srclist)).tolist()
        df['en'] = srclist
        df['{}'.format(lang)] = tgtlist

        csvpath = os.path.join(fpath, 'en-{}.xlsx'.format(lang))
        df.to_excel(csvpath, index=False)
    except Exception as e:
        print(lang, e)
        pass


 



            
            


