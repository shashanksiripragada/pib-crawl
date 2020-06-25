import os
import sys
sys.path.insert(1, '../')
from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request
from flask_migrate import Migrate
from datetime import datetime, timedelta 
from sqlalchemy import and_
from collections import Counter, defaultdict
from . import models as M
from . import db
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from tools.align import BLEUAligner
from cli import ILMULTI_DIR
from cli.utils import Preproc

segmenter = Segmenter()
root = os.path.join(ILMULTI_DIR, 'mm-all')
model='mm_all_iter0'
translator = mm_all(root=root, model=model, use_cuda=True).get_translator()
tokenizer = SentencePieceTokenizer()
aligner = BLEUAligner(translator, tokenizer, segmenter)
preproc = Preproc(segmenter, tokenizer)

from flask import Blueprint
from .retrieval import retrieve_neighbours_en 
docstore = Blueprint('docstore', __name__, template_folder='templates')

@docstore.route('/')
@docstore.route('/entry/<id>')
def entry(id):
    x =  M.Entry.query.get(id)
    models = ['mm_toEN_iter1', 'mm_all_iter1', 'mm_all_iter0']
    group = defaultdict(list)
    for model in models:
        retrieved = retrieve_neighbours_en(x.id, model=model)
        group[model] = retrieved
    return render_template('entry.html', entry=x, retrieved=group)

@docstore.route('/entry', methods=['GET'])
def listing():
    lang = request.args.get('lang', 'hi')
    x = db.session.query(M.Entry)\
            .filter(M.Entry.lang == lang)\
            .all()
    entries = set()
    date_aligned = 0    
    for entry in x:
        if entry.neighbors:
            links = entry.neighbors
            for link in links:
                if link.second.lang=='en':
                    entries.add(entry)
                    date_aligned+=1
    entries = list(entries)
    print(date_aligned)
    return render_template('listing.html', entries=entries)


@docstore.route('/parallel')
def parallel():
    src = request.args.get('src')
    tgt = request.args.get('tgt')
    src_entry =  M.Entry.query.get(src)
    tgt_entry =  M.Entry.query.get(tgt)
    def wrap_in_para(text):
        lines = text.splitlines()
        wrap = lambda l: '<p>{}</p>'.format(l)
        lines = list(map(wrap, lines))
        return '\n'.join(lines)
    src_entry.content = wrap_in_para(src_entry.content)
    tgt_entry.content = wrap_in_para(tgt_entry.content) 
    return render_template('parallel.html', entries=[src_entry,tgt_entry])


@docstore.route('/parallel/align')
def parallel_align():
    src = request.args.get('src')
    tgt = request.args.get('tgt')
    galechurch = request.args.get('galechurch', 'False')
    src_entry =  M.Entry.query.get(src)
    tgt_entry =  M.Entry.query.get(tgt)

    translation, alignments = aligner(src_entry.content, src_entry.lang, 
        tgt_entry.content, tgt_entry.lang, galechurch=(str(galechurch)=='True'))
    src_toks, hyp_toks = translation
    
    def detok(src_out):
        src = []
        for line in src_out:
            src_detok = tokenizer.detokenize(line)
            src.append(src_detok)
        return src

    def process(src_out, tgt_out):
        src = detok(src_out)
        tgt = detok(tgt_out)
        def wrap_pairwise(src, tgt):
            def create_individual(pair):
                src_line, tgt_line = pair
                fmt = '<div class="row" style="border:1px solid black; margin-bottom:1em;"><div class="col-6">{}</div><div class="col-6">{}</div></div>'.format(src_line,tgt_line)
                return fmt   
            rows = map(create_individual,zip(src, tgt))  
            rows = list(rows)    
            rows = '\n'.join(rows)
            return rows
        content = wrap_pairwise(src, tgt)
        return content
    #src_entry.content = '\n'.join(src)
    #tgt_entry.content = '\n'.join(tgt)
    translation_content = process(src_toks, hyp_toks)
    src_out, tgt_out = alignments
    aligned_content = process(src_out, tgt_out)
    def wrap_in_para(text):
        lines = text.splitlines()
        wrap = lambda l: '<p>{}</p>'.format(l)
        lines = list(map(wrap, lines))
        return '\n'.join(lines)
    src_entry.content = wrap_in_para(src_entry.content)
    tgt_entry.content = wrap_in_para(tgt_entry.content) 

    return render_template('parallel_translate.html', entries=[src_entry,tgt_entry],
                            translation_content=translation_content, 
                            aligned_content = aligned_content)


# @docstore.route('/entry2/<id>')
# def entry2(id):
#     x =  M.Entry.query.get(id)
#     delta = timedelta(days = 1)
#     start = x.date - delta
#     end = x.date + delta 
#     qry = M.Entry.query.filter(
#         and_(M.Entry.date <= end, M.Entry.date >= start , M.Entry.lang!=x.lang)).all()
#     print(len(qry))
#     lang_list = []
#     for i in qry:
#         lang_list.append(i.lang)
#     _list = Counter(lang_list).keys()
#     count = Counter(lang_list).values()
#     print(_list,'\n',count)
#     return render_template('entry.html', entry=x)

@docstore.route('/parallel/verify', methods=['GET', 'POST'])
def parallel_verify():
    if request.method == "POST":
        #print(request.args.get('src'))
        return "hello, {}".format(request.args.get('src'))
    else:
        src = request.args.get('src')
        tgt = request.args.get('tgt')
        src_entry =  M.Entry.query.get(src)
        tgt_entry =  M.Entry.query.get(tgt)
        def wrap_in_para(text):
            lines = text.splitlines()
            wrap = lambda l: '<p>{}</p>'.format(l)
            lines = list(map(wrap, lines))
            return '\n'.join(lines)
        src_entry.content = wrap_in_para(src_entry.content)
        tgt_entry.content = wrap_in_para(tgt_entry.content) 
        
        return render_template('verify.html', entries=[src_entry,tgt_entry])