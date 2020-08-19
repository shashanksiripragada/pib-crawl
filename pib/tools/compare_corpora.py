import os
import glob
from collections import defaultdict
from argparse import ArgumentParser
from itertools import combinations, permutations
import string
from ilmulti.translator import from_pretrained
import numpy as np
import kenlm

# engine = from_pretrained(tag='mm-to-en-iter2', use_cuda=False)
# segmenter = engine.segmenter
# tokenizer = engine.tokenizer

def ilci_stats(corpora_dir):
    #langs = ['en', 'hi', 'ta', 'te', 'ml', 'ud', 'bg', 'gj', 'mr', 'kn', 'pj']
    langs = ['en', 'hi', 'ta', 'te', 'ml', 'ud', 'bg']
    vocab, corpus = set(), set()
    lenghts = []
    for xx in langs:
        fpath = os.path.join(corpora_dir)
        fname = 'complete'
        srcfile = open('{}/{}.{}'.format(fpath, fname, xx), 'r')
        if xx=='pj': xx='pa'
        if xx=='bg': xx='bn'
        if xx=='ud': xx='ur'
        if xx=='gj': xx='gu'
        out = open('ilci_tok.txt', 'a')
        for sline  in srcfile:
            sline = sline.rstrip()
            sline = sline.split()
            #_, content = tokenizer(sline, lang=xx)
            #print(' '.join(content), file=out)
            vocab.update(sline)
            lenghts.append(len(sline))
    print(corpora_dir)    
    print('mean sent length' , np.mean(lenghts))
    print('median sent length', np.median(lenghts))
    print('vocab', len(vocab))

def pib_stats(corpora_dir):
    #out = open('pib_tok.txt', 'a')
    #langs = ['en','hi','ta', 'te' ,'ml', 'ur', 'bn', 'gu', 'mr','or' ,'pa']
    langs = ['en', 'hi', 'ta', 'te' , 'ml', 'ur', 'bn']
    langs = sorted(langs)
    perm = combinations(langs, 2)
    vocab = set()
    corpus = set()
    lengths = []

    for xx, yy in list(perm):
        if  'en' in [xx, yy]:
            fpath = os.path.join(corpora_dir, '{}-{}'.format(xx, yy))
            fname = 'train'
            srcfile = open('{}/{}.{}'.format(fpath, fname, xx), 'r')
            tgtfile = open('{}/{}.{}'.format(fpath, fname, yy), 'r')
            for sline, tline  in zip(srcfile, tgtfile):
                sline, tline = sline.rstrip(), tline.rstrip()                    
                sline, tline = sline.split(), tline.split()
                lengths.append(len(sline))
                lengths.append(len(tline))
                #_, scontent = tokenizer(sline, lang=xx)
                #_, tcontent = tokenizer(tline, lang=yy)
                #print(' '.join(scontent), file=out)
                #print(' '.join(tcontent), file=out)
                vocab.update(sline)
                vocab.update(tline)        
    print(corpora_dir)    
    print('mean sent length', np.mean(lengths))
    print('median sent length', np.median(lengths))
    print('vocab', len(vocab))

def wat_stats(corpora_dir):
    #out = open('wat_tok.txt', 'a')
    langs = ['hi','ta', 'te' ,'ml', 'ur', 'bn']
    vocab = set()
    corpus = set()
    lengths = []
    for xx in langs:
        fpath = os.path.join(corpora_dir, '{}-{}'.format(xx, 'en'))
        fname = 'train'
        srcfile = open('{}/{}.{}'.format(fpath, fname, xx), 'r')
        tgtfile = open('{}/{}.{}'.format(fpath, fname, 'en'), 'r')
        for sline, tline  in zip(srcfile, tgtfile):
            sline, tline = sline.rstrip(), tline.rstrip()
            #_, scontent = tokenizer(sline, lang=xx)
            #_, tcontent = tokenizer(tline, lang='en')
            #print(' '.join(scontent), file=out)
            #print(' '.join(tcontent), file=out)                    
            sline, tline = sline.split(), tline.split()
            lengths.append(len(sline))
            lengths.append(len(tline))
            vocab.update(sline)
            vocab.update(tline)
    print(corpora_dir)
    print('mean sent length', np.mean(lengths))
    print('median sent length', np.median(lengths))
    print('vocab', len(vocab))


def evaluate(corpus, model):
    ppls = []
    file = open('lmeval/{}_tok_uniq.txt'.format(corpus), 'r')
    lm = kenlm.Model('lmeval/{}.binary'.format(model))
    for line in file:
        ppl = lm.perplexity(line.rstrip())
        ppls.append(ppl)
    print('lm :{}'.format(model), 'corpus :{}'.format(corpus), np.median(ppls))


def compute_perplexity():
    models = ['ilci', 'pib', 'wat']
    models = sorted(models)
    corpora = models
    ls = [(corpus, model) for corpus in corpora for model in models] 
    for (corpus, model) in ls:
        evaluate(corpus, model)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--ilci', type=str, required=True)
    parser.add_argument('--pib', type=str, required=True)
    parser.add_argument('--wat', type=str, required=True)
    args = parser.parse_args()
    ilci_stats(args.ilci)
    pib_stats(args.pib)
    wat_stats(args.wat)
    compute_perplexity()