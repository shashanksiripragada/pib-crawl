import sys
import os
import numpy as np
sys.path.insert(1, os.getcwd())
sys.path.insert(1, '../')
from webapp import db
from io import StringIO
from webapp.models import Entry, Link, Translation, Retrieval
from ilmulti.segment import Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
from utils import Preproc
from tqdm import tqdm
from argparse import ArgumentParser
from sqlalchemy import func, and_
from urduhack.tokenization import sentence_tokenizer
langs = ['hi', 'ta', 'te', 'ml', 'ur', 'bn', 'gu', 'mr', 'pa', 'or']

segmenter = Segmenter()


def paralle_write(src_entry, src_lang):
    print(src_entry,file=src_file)


def export(src_lang):
    entries = db.session.query(Entry).filter(Entry.lang==src_lang).all()
    for entry in tqdm(entries):
        print(entry.id)
        lang, segments = segmenter(entry.content, lang=src_lang)
        output = '\n'.join(segments)
        print(output)
        break


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('src_lang', help='language of mono corpus')
    args = parser.parse_args()
    src_lang = args.src_lang
    src_file = open('pib_mono.{}.txt'.format(src_lang),'a')
    export(src_lang)

