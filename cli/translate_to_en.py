import time
import numpy as np
import langid
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from datetime import timedelta 
import datetime
from webapp import db
from webapp.models import Entry, Link, Translation, Retrieval
from sqlalchemy import func
import itertools
from tqdm import tqdm
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
import os
from ilmulti.utils.language_utils import inject_token
import csv
from collections import namedtuple, defaultdict
from sqlalchemy import and_
from ilmulti.align import BLEUAligner
from io import StringIO

segmenter = Segmenter()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
translator.cuda()
tokenizer = SentencePieceTokenizer()
aligner = BLEUAligner(translator, tokenizer, segmenter)

def process(content, tgt_lang):
    lang, content = segmenter(content)
    output = []
    for line in content:
        if line:
            lang, _tokens = tokenizer(line)
            _out = ' '.join(_tokens)
            output.append(_out)        
    injected_toks = inject_token(output,tgt_lang)
  
    return injected_toks 

def detok(src_out):
    src = []
    for line in src_out:
        src_detok = tokenizer.detokenize(line)
        src.append(src_detok)
    return src   

langs = ['hi','ml','bn','te','ta','ur']
model = 'mm_all'
error = open('retrieval_error.txt','w+')


#translate()

langs = ['en', 'ml', 'ur', 'te', 'hi', 'pa', 'kn', 'or', 'as', 'gu', 'mr', 'ta', 'bn']

def get_sents():
    sents = dict.fromkeys(langs,0)
    matches = db.session.query(Entry) \
        .filter(Entry.lang.in_(langs)) \
        .all()
    for match in matches:
        if match.content:
            content_ = match.content.splitlines()
            count = sents[match.lang]
            count += len(content_)
            sents[match.lang] = count

    print(sents)

def create_stringio(lines, lang):
    tokenized = [ ' '.join(tokenizer(line, lang=lang)[1]) \
            for line in lines ]
    lstring = '\n'.join(tokenized)
    return tokenized, StringIO(lstring)

def process(content, lang):
    lang, segments = segmenter(content, lang=lang)
    tokenized, _io = create_stringio(segments, lang)
    return tokenized, _io

def detok(src_out):
    src = []
    for line in src_out:
        src_detok = tokenizer.detokenize(line)
        src.append(src_detok)
    return src

langs = ['ml', 'ur', 'te', 'hi', 'ta', 'bn']
src_lan = 'ur' 
tgt_lan = 'en'
src_file = open('pib_en-{}.{}.txt'.format(src_lan,src_lan),'a')
tgt_file = open('pib_en-{}.{}.txt'.format(src_lan,tgt_lan),'a')

def paralle_write(src,src_lang,tgt,tgt_lang,article_no):
    print('##########Article {} #########'.format(article_no),file=src_file)
    print(src,file=src_file)
    print('##########Article {} #########'.format(article_no),file=tgt_file)
    print(tgt,file=tgt_file)

def init_align():
    ids = db.session.query(Retrieval)
    count = dict.fromkeys(langs,0)
    scores = dict.fromkeys(langs,0)
    article_no = 0
    for i in tqdm(ids):
        q = i.query_id
        r = i.retrieved_id
        qlang = db.session.query(Entry.lang).filter(Entry.id==q).first().lang
        score = i.score
        date_link = db.session.query(Link.second_id).filter(Link.first_id==q).distinct().all()
        for link in date_link:
            rlang = db.session.query(Entry.lang).filter(Entry.id==link.second_id).first().lang
            if rlang=='en' and qlang=='{}'.format(src_lan) and link.second_id==r:
                src = db.session.query(Entry.content).filter(Entry.id==q).first().content
                src_lang = db.session.query(Entry.lang).filter(Entry.id==q).first().lang
                tgt = db.session.query(Entry.content).filter(Entry.id==r).first().content
                tgt_lang = db.session.query(Entry.lang).filter(Entry.id==r).first().lang
                hyp = db.session.query(Translation.translated).filter(Translation.parent_id==q)\
                                .first().translated
                src , src_io = process(src, src_lang)
                tgt , tgt_io = process(tgt, tgt_lang)
                hyp , hyp_io = create_stringio(hyp, tgt_lang)
                src , tgt = aligner.bleu_align(src_io, tgt_io, hyp_io)
                src = detok(src)
                tgt = detok(tgt)               
                src_entry = '\n'.join(src)
                tgt_entry = '\n'.join(tgt)
                article_no += 1
                paralle_write(src_entry,src_lang,tgt_entry,tgt_lang,article_no)
                


                
                '''
                cnt = count[qlang]
                cnt += 1            
                count[qlang] = cnt
                scr = scores[qlang]
                scr+=score
                scores[qlang]=scr
              
    #print(count)
    for lang in scores:
        av = scores[lang]/count[lang]
        print(lang,av)
                    '''
init_align()
