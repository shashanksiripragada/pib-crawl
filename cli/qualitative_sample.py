import random
import csv
from collections import defaultdict
import os
import pandas as pd
import numpy as np
common = defaultdict(list)

random.seed(5)

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
            open(os.path.join(fpath, '{}.{}'.format('test', xx)), 'w'),
            open(os.path.join(fpath, '{}.{}'.format('test', yy)), 'w')
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
    langs = ['hi', 'ta', 'te', 'ml', 'ur', 'gu', 'mr', 'or', 'pa']
    langs = ['mr']
    for lang in langs:
        try:
            fpath = './'.format(lang)
            srcpath = os.path.join(fpath, '{}'.format('pib_en-mr.mr.filt.txt'))
            tgtpath = os.path.join(fpath, '{}'.format('pib_en-mr.en.filt.txt'))

            srcfile, tgtfile = get_fp(srcpath, tgtpath)    
            srclines = get_size(srcfile)
            tgtlines = get_size(tgtfile)
            samples = random.sample(range(0,srclines), 100)
            
            pwriter = ParallelWriter(fpath)
            srcfile, tgtfile = get_fp(srcpath, tgtpath)   
            srclist, tgtlist = get_samples('en', lang, srcfile, tgtfile, samples)


            for src, tgt in zip(srclist, tgtlist):
                pwriter.write(lang,'en', src, tgt)
           
        except Exception as e:
            print(lang, e)
            pass


 



            
            


