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
from ilmulti.align import BLEUAligner

segmenter = Segmenter()
root = '/home/darth.vader/.ilmulti/mm-all'
translator = mm_all(root=root).get_translator()
tokenizer = SentencePieceTokenizer()
aligner = BLEUAligner(translator, tokenizer, segmenter)

from flask import Blueprint
from .retrieval import retrieve_neighbours 
docstore = Blueprint('docstore', __name__, template_folder='templates')

@docstore.route('/')
@docstore.route('/entry/<id>')
def entry(id):
    x =  M.Entry.query.get(id)    
    retrieved = retrieve_neighbours(x.id)
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
    return render_template('parallel.html', entries=[src_entry,tgt_entry])


@docstore.route('/parallel/align')
def parallel_align():
    src = request.args.get('src')
    tgt = request.args.get('tgt')
    src_entry =  M.Entry.query.get(src)
    tgt_entry =  M.Entry.query.get(tgt)
    src_out, tgt_out = aligner(src_entry.content, src_entry.lang, 
        tgt_entry.content, tgt_entry.lang)
    def detok(src_out):
        src = []
        for line in src_out:
            src_detok = tokenizer.detokenize(line)
            src.append(src_detok)
        return src

    src = detok(src_out)
    tgt = detok(tgt_out)
    
    src_entry.content = '\n'.join(src)
    tgt_entry.content = '\n'.join(tgt)
    return render_template('parallel.html', entries=[src_entry,tgt_entry])


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
