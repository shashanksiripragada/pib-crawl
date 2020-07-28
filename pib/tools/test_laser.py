from laserembeddings import Laser
from numpy import dot
from numpy.linalg import norm

def cos_sim(a,b):
    cos_sim = dot(a, b)/(norm(a)*norm(b))
    return cos_sim

path_to_bpe_codes = '/home/darth.vader/laser/93langs.fcodes'
path_to_bpe_vocab = '/home/darth.vader/laser/93langs.fvocab'
path_to_encoder = '/home/darth.vader/laser/bilstm.93langs.2018-12-26.pt'

laser = Laser(path_to_bpe_codes, path_to_bpe_vocab, path_to_encoder)


emb = laser.embed_sentences(
    ['how are you'],
    lang='en') 

te_emb = laser.embed_sentences(
    ['क्या हाल है'],
    lang='hi')  

sim = cos_sim(emb[0],te_emb[0])
print(sim)


import time
import numpy as np
import langid
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
import datetime
from .. import db
from ..models import Entry, Link, Translation
from sqlalchemy import func
import itertools
from tqdm import tqdm
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
import os
from ilmulti.utils.language_utils import inject_token

segmenter = Segmenter()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
translator.cuda()
tokenizer = SentencePieceTokenizer()
#aligner = BLEUAligner(translator, tokenizer, segmenter)

def process(content,tgt_lang):
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
error = open('translate_error.txt','w+')

def translate():
    entries = db.session.query(Entry.id,Entry.lang,Entry.date,Entry.content)\
                .filter(Entry.lang.in_(langs)).all()
    tgt_lang = 'en'
    for entry in tqdm(entries):
        if entry.content:
            src_tok = process(entry.content,tgt_lang=tgt_lang)
            out = translator(src_tok)
            hyps = [ gout['tgt'] for gout in out ]
            hyps = detok(hyps)
            translated = '\n'.join(hyps)
            entry = Translation(parent_id= entry.id, model= model, lang= tgt_lang, translated= translated)
            exists = db.session.query(Translation.id).first()
            if not exists:
                try:
                    db.session.add(entry)
                    db.session.commit()
                except:
                    print(entry.id,fp=error)

translate()
