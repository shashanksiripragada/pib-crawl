import os
import sys
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
from ilmulti.sentencepiece import build_tokenizer
from tools.align import BLEUAligner

segmenter = Segmenter()
tokenizer = build_tokenizer('ilmulti-v0')

from flask import Blueprint
from .retrieval import retrieve_neighbours_en 

docstore = Blueprint('docstore', __name__, template_folder='templates')

@docstore.route('/')
@docstore.route('/entry/<id>')
def entry(id):
    x =  M.Entry.query.get(id)

    # Replace model: str with models table.

    models = ['mm_toEN_iter1', 'mm_all_iter1', 'mm_all_iter0']
    group = defaultdict(list)

    for model in models:
        retrieved = retrieve_neighbours_en(x.id, model=model)
        group[model] = retrieved

    return render_template('entry.html', entry=x, retrieved=group)

@docstore.route('/entry', methods=['GET'])
def listing():
    lang = request.args.get('lang', 'hi')

    # TODO: optimize the below routine.
    x = (
        db.session.query(M.Entry)
            .filter(M.Entry.lang == lang)
            .all()
    )

    entries = set()
    for entry in x:
        if entry.neighbors:
            links = entry.neighbors
            for link in links:
                if link.second.lang=='en':
                    entries.add(entry)

    entries = list(entries)
    return render_template('listing.html', entries=entries)


@docstore.route('/parallel')
def parallel():
    def process(key):
        param = request.arg.get(key)
        entry = M.entry.query.get(param)
        content = split_and_wrap_in_p(entry.content)
        return content

    entries = list(map(process, ['src', 'tgt']))
    return render_template('parallel.html', entries=entries)


@docstore.route('/parallel/align')
def parallel_align():
    src = request.args.get('src')
    tgt = request.args.get('tgt')
    galechurch = request.args.get('galechurch', 'False')

    src_entry =  M.Entry.query.get(src)
    tgt_entry =  M.Entry.query.get(tgt)

    aligner = get_aligner()
    translation, alignments = aligner(
        src_entry.content, src_entry.lang, 
        tgt_entry.content, tgt_entry.lang, 
        galechurch=(str(galechurch)=='True')
    )

    src_toks, hyp_toks = translation
    
    from .utils import detok

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

    src_entry.content = split_and_wrap_in_p(src_entry.content)
    tgt_entry.content = split_and_wrap_in_p(tgt_entry.content) 

    return render_template('parallel_translate.html', entries=[src_entry,tgt_entry],
                            translation_content=translation_content, 
                            aligned_content = aligned_content)


@docstore.route('/parallel/verify', methods=['GET', 'POST'])
def parallel_verify():
    if request.method == "POST":
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
