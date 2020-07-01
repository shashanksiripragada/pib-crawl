import os
import sys

from datetime import datetime, timedelta 
from collections import Counter, defaultdict

from flask import Flask, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request
from flask_migrate import Migrate
from flask import Blueprint
from sqlalchemy import and_
from . import models as M
from . import db
from .models import Entry, Link, Titles
from .retrieval import retrieve_neighbours_en, retrieve_neighbours
from .utils import split_and_wrap_in_p, clean_translation, detok

from ilmulti.translator import from_pretrained
from tools.align import BLEUAligner

op_model = from_pretrained(tag='mm-to-en-iter1', use_cuda=True)
aligner = BLEUAligner(
    op_model.translator, op_model.tokenizer,
    op_model.segmenter
)

docstore = Blueprint('docstore', __name__, template_folder='templates')

@docstore.route('/')
@docstore.route('/entry/<id>')
def entry(id):
    x =  M.Entry.query.get(id)

    # Replace model: str with models table.
    # models = ['mm-to-en-iter1', 'mm_toEN_iter1', 'mm_all_iter1', 'mm_all_iter0']
    models = ['mm-all-iter1', 'mm-to-en-iter1']

    group = defaultdict(list)

    x.content = split_and_wrap_in_p(x.content)

    if x.lang != 'en':
        for model in models:
            if model=='mm-all-iter1':
                pivot_lang='hi'
            else:
                pivot_lang='en'
            #retrieved = retrieve_neighbours_en(x.id, op_model.tokenizer, model=model)
            retrieved = retrieve_neighbours(
                            x.id,
                            pivot_lang=pivot_lang, 
                            tokenizer=op_model.tokenizer, 
                            model=model
                        )
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
        param = request.args.get(key)
        entry = M.Entry.query.get(param)
        entry.content = split_and_wrap_in_p(entry.content)
        return entry

    entries = list(map(process, ['src', 'tgt']))
    return render_template('parallel.html', entries=entries)


@docstore.route('/parallel/align')
def parallel_align():
    src = request.args.get('src')
    tgt = request.args.get('tgt')
    galechurch = request.args.get('galechurch', 'False')
    model = request.args.get('model', 'mm-to-en-iter1')

    src_entry =  M.Entry.query.get(src)
    tgt_entry =  M.Entry.query.get(tgt)


    translation, alignments = aligner(
        src_entry.content, src_entry.lang, 
        tgt_entry.content, tgt_entry.lang, 
        galechurch=(str(galechurch)=='True')
    )

    src_toks, hyp_toks = translation
    

    def process(src_out, tgt_out):
        src = detok(op_model.tokenizer, src_out)
        tgt = detok(op_model.tokenizer, tgt_out)
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

    query = (
        M.Translation.query.filter(
            and_(
                M.Translation.parent_id == src, 
                M.Translation.model == model
            )
        ).first()
    )

    if query:
        translated_text = clean_translation(op_model.tokenizer, query)

    stored_translation = translated_text if query else ''
    stored_translation = split_and_wrap_in_p(stored_translation)

    translation_content = process(src_toks, hyp_toks)
    src_out, tgt_out = alignments
    aligned_content = process(src_out, tgt_out)

    src_entry.content = split_and_wrap_in_p(src_entry.content)
    tgt_entry.content = split_and_wrap_in_p(tgt_entry.content) 


    return render_template(
            'parallel_translate.html', 
            entries=[src_entry,tgt_entry], 
            translation_content=translation_content, 
            aligned_content=aligned_content,
            stored_translation=stored_translation
    )

@docstore.route('/stored-translations/<entry_id>')
def stored_translations(entry_id):
    entry =  M.Entry.query.get(entry_id)
    translations = (
        M.Translation.query.filter(
            M.Translation.parent_id == entry_id, 
        ).all()
    )

    for translation in translations:
        cleaned = clean_translation(op_model.tokenizer, translation)
        translation.translated = split_and_wrap_in_p(cleaned)

    return render_template('stored_translations.html', entry=entry, translations=translations)

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
