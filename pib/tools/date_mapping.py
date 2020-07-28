import time
import numpy as np
import langid
from ilmulti.segment import SimpleSegmenter, Segmenter
from ilmulti.sentencepiece import SentencePieceTokenizer
import datetime
from .. import db
from ..models import Entry, Link
from sqlalchemy import func
import itertools
from tqdm import tqdm
import nltk
from ilmulti.translator.pretrained import mm_all
from bleualign.align import Aligner
import os

del_id=50
del_time=1
datetimeFormat = '%Y-%m-%d %H:%M:%S'

'''
def get_mapping():
	rows = Entry.query.order_by(Entry.date.desc()).filter_by(lang='en').all()
	for row in rows:
		year = row.date.strftime("%Y")
		time = str(row.date)
		for q in range(row.id-del_id,row.id+del_id):
			exists = Entry.query.filter(Entry.id==q).filter(Entry.lang!='en').first()
			if exists : #and row.city==exists.city :
				q_year = exists.date.strftime("%Y")
				q_time = str(exists.date)
				d1 = datetime.datetime.strptime(time, datetimeFormat)
				d2 = datetime.datetime.strptime(q_time, datetimeFormat)
				diff = d1-d2
				if abs(diff.days) <=10  and year==q_year and year==2019:
					print(row.id,exists.id)

#get_mapping()


		sent_text = nltk.sent_tokenize(row1.content)
		print(len(sent_text))
		for sent in sent_text:
			print(sent,'\n')


'''

'''
output = open('output.txt','w+')
outsrc = open('outsrc.txt','w+')
outtgt = open('outtgt.txt','w+')
srcfile = open('srcfile.txt','r')
tgtfile = open('tgtfile.txt','r')
hyp_src_tgt_file = open('hyp_src_tgt_file.txt','r')
'''


segmenter = Segmenter()
translator = mm_all()
tokenizer = SentencePieceTokenizer()

def get_tokenized(content):
	untok = []
	tok = []
	for line in content:
		lines = line.splitlines()
		for l in lines:
			untok.append(l) #untokenized 
			lang, _out = tokenizer(l)
			tokens = ' '.join(_out) #tokenized
			tok.append(tokens)
	return untok, tok


def ifexists():
	hyp_src_tgt = []
	row1=Entry.query.filter_by(id=1580832).first()
	if row1:
		content = segmenter(row1.content)[1]
		untok, tok = get_tokenized(content)
		tgt = tok
	row=Entry.query.filter_by(id=1580904).first()
	if row:
		content = segmenter(row.content)[1]
		untok, tok = get_tokenized(content)
		src = tok
		for sent in untok:
			output = translator(sent,tgt_lang='en')[0]['tgt']
			hyp_src_tgt.append(output)
			lang, _out = tokenizer(output)
			tokens = ' '.join(_out)
			hyp_src_tgt = tokens
	align(src,tgt,hyp_src_tgt)		
#ifexists()




#### Pairs based on same posted date  
def findpairs():
	dups = db.session.query(Entry.date,func.count(Entry.id).label('freq')).\
						group_by(Entry.date).\
						subquery()
	pair = db.session.query(Entry.id,Entry.lang,Entry.date,dups.c.freq).\
						outerjoin(dups,Entry.date==dups.c.date).\
						filter(dups.c.freq>1).\
						order_by(Entry.date).\
						all()
	mapping = {}
	for p in pair:
		if p.date not in mapping:
			mapping[p.date] = [p.id]
		else:
			mapping[p.date].append(p.id)
	
	l = list(mapping.values())
	for bunch in tqdm(l):
		z=itertools.permutations(bunch,2)
		z = list(z)
		for (x,y) in z:
			link = Link(first_id=x,second_id=y)
			db.session.add(link)
			db.session.commit()

#findpairs()

