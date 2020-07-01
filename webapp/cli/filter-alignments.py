from io import StringIO
from tqdm import tqdm
from argparse import ArgumentParser

from ilmulti.translator import from_pretrained
from .utils import Preproc

import langid
from langid.langid import LanguageIdentifier
from langid.langid import model as m

def parallel_write(src_lang, src_entry, tgt_lang, tgt_entry):
    src_out = open('train.en-{}.{}'.format(src_lang, src_lang),'a')
    tgt_out = open('train.en-{}.{}'.format(src_lang, tgt_lang),'a')
    print(src_entry,file=src_out)
    print(tgt_entry,file=tgt_out)

def eval_len_ratio(src_len, tgt_len):
    if src_len==0 or tgt_len==0:
        return False
    ratio = src_len/tgt_len
    src = (src_len >=2)
    tgt = (tgt_len >=2)
    if 0.5 <= ratio <= 2 and src and tgt:
        return True

def eval_lang(src_lang, src_line, tgt_lang, tgt_line):
    threshold = 0.8
    slang, src_prob = identifier.classify(src_line)
    tlang, tgt_prob = identifier.classify(tgt_line)
    src = (src_prob >= threshold)
    tgt = (tgt_prob >= threshold)
    if slang==src_lang and tlang==tgt_lang and src and tgt:
        return True
    else:
        return False

def filter_lines(src_lang, src_file, tgt_lang, tgt_file):
    src_uniq = set()
    tgt_uniq = set()
    for src_line, tgt_line in zip(src_file, tgt_file):
        src_len = len(src_line.split())
        tgt_len = len(tgt_line.split())
        len_eval = eval_len_ratio(src_len, tgt_len)
        lang_eval = eval_lang(src_lang, src_line, tgt_lang, tgt_line)
        if len_eval and lang_eval :
            src_line = src_line.rstrip('\n')
            tgt_line = tgt_line.rstrip('\n')
            if src_line not in src_uniq and tgt_line not in tgt_uniq:
                src_uniq.add(src_line)
                tgt_uniq.add(tgt_line)
                parallel_write(src_lang, src_line, tgt_lang, tgt_line)

if __name__ == '__main__':
    parser=ArgumentParser()
    parser.add_argument('--src_lang', help='source language, non-english', required=True)
    parser.add_argument('--tgt_lang', help='target language', required=True )
    parser.add_argument('--model', help='translation model for generating dataset', required=True)

    # engine = from_pretrained(tag=model, use_cuda=False)
    # preproc = Preproc(engine.segmenter, engine.tokenizer)

    args = parser.parse_args()
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    model = args.model

    src_file = open('pib_{}_en-{}.{}.txt'.format(model, src_lang, src_lang),'r')
    tgt_file = open('pib_{}_en-{}.{}.txt'.format(model, src_lang, tgt_lang),'r')

    identifier = LanguageIdentifier.from_modelstring(m, norm_probs=True)
    identifier.set_languages(['{}'.format(src_lang),'{}'.format(tgt_lang)])
    
    filter_lines(src_lang, src_file, tgt_lang, tgt_file)

