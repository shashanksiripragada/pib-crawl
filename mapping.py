import mysql.connector as mysql
import time
import numpy as np
import langid
from lmdbcache import LMDBCacheContextManager
lmdbpath = "inserted"
import datetime
#from datetime import datetime
from webapp import db
from webapp.models import Entry

'''
def rewrite(entry):
	_id, text, *rest = entry
	date, day, month, year, time, *rest = rest
	place, lang, clean = rest
	exists = Entry.query.filter_by(id=_id).first()

	if exists:
		return

	from datetime import datetime

	dstr = f'{month} {day} {year} {time}'
	#print(dstr)
	date = datetime.strptime(dstr, '%b %d %Y %I:%M%p')


	#date = process(day, month, year, time)
	# create objects

	e = Entry(
		id = _id,
		content = clean,
		date = date,
		city = place,
		lang = lang
	)

	db.session.add(e)
	db.session.commit()
'''
del_id=50
del_time=1
datetimeFormat = '%Y-%m-%d %H:%M:%S'

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

get_mapping()

def ifexists():
	row1=Entry.query.filter_by(id=1520841).first()
	if row1:
		print(row1.content)
	row=Entry.query.filter_by(id=1520946).first()
	if row:
		print(row.content)

#ifexists()