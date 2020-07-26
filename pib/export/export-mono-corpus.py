import os
import numpy as np
from io import StringIO

from .. import db
from ..models import Entry, Link, Translation, Retrieval

from .utils import Preproc

from ilmulti.segment import Segmenter
from ilmulti.translator import from_pretrained

from tqdm import tqdm
from argparse import ArgumentParser
from sqlalchemy import func, and_

def write(src_entry, src_lang):
    print(src_entry,file=src_file)


def export(src_lang):
    uniq = set()
    entries = db.session.query(Entry).filter(Entry.lang==src_lang).all()
    for entry in tqdm(entries):
        if entry.content:
            lang, segments = segmenter(entry.content, lang=src_lang)
            uniq.update(segments)

    print(len(uniq))
        #output = '\n'.join(segments)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--src_lang', help='language of mono corpus', required=True)
    args = parser.parse_args()
    src_lang = args.src_lang

    engine = from_pretrained(tag='mm-to-en-iter1', use_cuda=False)
    segmenter = engine.segmenter

    src_file = open('pib_mono.{}.txt'.format(src_lang),'a')
    export(src_lang)

