import sys
sys.path.insert(1, '../')
from io import StringIO
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from utils import detok, process, create_stringio
from tqdm import tqdm
from argparse import ArgumentParser
import langid

from langid.langid import LanguageIdentifier, model
identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)

#langs = ['en', 'ml', 'ur', 'te', 'hi', 'pa', 'kn', 'or', 'as', 'gu', 'mr', 'ta', 'bn']

#segmenter = Segmenter()
#tokenizer = SentencePieceTokenizer()
#root = '/home/darth.vader/.ilmulti/mm-all'
#translator = mm_all(root=root).get_translator()
#translator.cuda()
#aligner = BLEUAligner(translator, tokenizer, segmenter)



def parallel_write(src_lang, src_entry, tgt_lang, tgt_entry):
    src_out = open('./pib/filtered/pib_en-{}.{}.filt.txt'.format(src_lang, src_lang),'a')
    tgt_out = open('./pib/filtered/pib_en-{}.{}.filt.txt'.format(src_lang, tgt_lang),'a')
    print(src_entry,file=src_out)
    print(tgt_entry,file=tgt_out)

def eval_len_ratio(src_len, tgt_len):
    if src_len==0 or tgt_len==0:
        return False
    ratio = src_len/tgt_len
    src = (src_len >=2)#(2 <= src_len <= 50)
    tgt = (tgt_len >=2)#(2 <= tgt_len <= 50)
    if 0.5 <= ratio <= 2 and src and tgt:
        return True

def eval_lang(src_lang, src_line, tgt_lang, tgt_line):
    threshold = 0.9
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
    parser.add_argument('src_lang', help='non-english language')
    parser.add_argument('tgt_lang', help='english is the target language')
    #parser.add_argument('src_file', help='src file')
    #parser.add_argument('tgt_file', help='src file to write the alignments into')
    args = parser.parse_args()
    src_lang, tgt_lang = args.src_lang, args.tgt_lang
    src_file = open('pib_en-{}.{}.txt'.format(src_lang, src_lang),'r')
    tgt_file = open('pib_en-{}.{}.txt'.format(src_lang, tgt_lang),'r')

    identifier.set_languages(['{}'.format(src_lang),'{}'.format(tgt_lang)])
    filter_lines(src_lang, src_file, tgt_lang, tgt_file)

'''
class CleanCorpus:
    def __init__(self, src_lang, tgt_lang):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if 
        batch = self.next_batch()
        return batch


    def evaluate_pair(self, src_line, tgt_line):
        src_len = len(src_line.split())
        tgt_len = len(tgt_line.split())
        if src_len==0 or tgt_len==0:
            return False
        ratio = src_len/tgt_len
        slang, _ = langid.classify(src_line)
        tlang, _ = langid.classify(tgt_line)
        if (slang, tlang)==(self.src_lang, self.tgt_lang) and 0.5 <= ratio <= 1.5:
            return True
        



    def __call__(self, src_in, tgt_in, src_out, tgt_out):
        for src_line, tgt_line in zip(src_in, tgt_in):
            if self.evaluate_pair(src_line, tgt_line):
                src_line = src_line.rstrip('\n')
                tgt_line = tgt_line.rstrip('\n')
                yield src_line
                self.parallel_write(src_lang, src_line, tgt_lang, tgt_line)

corpus = CleanCorpus(src_lang, tgt_lang)
src, tgt = corpus(src_file, tgt_file)

def parallel_write(self, src_out, tgt_out):
    print(src_entry,file=src_file)
    print(tgt_entry,file=tgt_file)
'''