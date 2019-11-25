import sys
sys.path.insert(1, '../')
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request
from flask_migrate import Migrate
from datetime import datetime, timedelta 
from sqlalchemy import and_
from collections import Counter
from . import models as M
from . import db
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
from ilmulti.translator.pretrained import mm_all
from tools.align import BLEUAligner

segmenter = Segmenter()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
tokenizer = SentencePieceTokenizer()
aligner = BLEUAligner(translator, tokenizer, segmenter)

from flask import Blueprint
from .retrieval import retrieve_neighbours_en 
docstore = Blueprint('docstore', __name__, template_folder='templates')

@docstore.route('/')
@docstore.route('/entry/<id>')
def entry(id):
    x =  M.Entry.query.get(id)    
    retrieved = retrieve_neighbours_en(x.id)
    return render_template('entry.html', entry=x, retrieved=retrieved)

@docstore.route('/entry', methods=['GET'])
def listing():
    lang = request.args.get('lang', 'hi')
    x = (db.session.query(M.Entry)
            .filter(M.Entry.id == M.Translation.parent_id)
            .filter(M.Entry.lang == lang)
            .all()
            # .limit(200)
        )
    return render_template('listing.html', entries=x)


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
    src_entry =  M.Entry.query.get(src)
    tgt_entry =  M.Entry.query.get(tgt)
    translation, alignments = aligner(src_entry.content, src_entry.lang, 
        tgt_entry.content, tgt_entry.lang)
    src_toks, hyp_toks = translation
    src_out, tgt_out = alignments
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
                fmt = '<div class="row" style="border:1px solid black;"><div class="col-6">{}</div><div class="col-6">{}</div></div>'.format(src_line,tgt_line)
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
    aligned_content = process(src_out, tgt_out)
    return render_template('parallel_translate.html', entries=[src_entry,tgt_entry],
                            translation_content=translation_content, 
                            aligned_content = aligned_content)


@docstore.route('/entry2/<id>')
def entry2(id):
    x =  M.Entry.query.get(id)
    delta = timedelta(days = 1)
    start = x.date - delta
    end = x.date + delta 
    qry = M.Entry.query.filter(
        and_(M.Entry.date <= end, M.Entry.date >= start , M.Entry.lang!=x.lang)).all()
    print(len(qry))
    lang_list = []
    for i in qry:
        lang_list.append(i.lang)
    _list = Counter(lang_list).keys()
    count = Counter(lang_list).values()
    print(_list,'\n',count)
    return render_template('entry.html', entry=x)
