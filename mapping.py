import mysql.connector as mysql
import time
import numpy as np
import langid
from lmdbcache import LMDBCacheContextManager
lmdbpath = "inserted"

from webapp import db
from webapp.models import Mapping

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

# print(text)


mdb = mysql.connect(
  host='localhost',
  user='root',
  database='pibscrape'
)


cursor = mdb.cursor()
query = 'SELECT * FROM data'
cursor.execute(query)

with open('failed.txt','w+') as fp:
	for x in cursor:

		try:
			rewrite(x)
		except:
			print(x[0],file=fp)



