import sys
sys.path.insert(1, '../')
from urllib.request import Request, urlopen
import time
import numpy as np
import langid
from tqdm import tqdm
from webapp import db
from webapp.models import Entry, Titles

def rewrite(entry):
	_id, text, *rest = entry
	date, day, month, year, time, *rest = rest
	place, lang, clean = rest
	exists = Entry.query.filter_by(id=_id).first()

	if exists:
		return

	from datetime import datetime

	dstr = f'{month} {day} {year} {time}'
	date = datetime.strptime(dstr, '%b %d %Y %I:%M%p')

	e = Entry(
		id = _id,
		content = clean,
		date = date,
		city = place,
		lang = lang
	)

	db.session.add(e)
	db.session.commit()

# mdb = mysql.connect(
#   host='localhost',
#   user='root',
#   database='pibscrape'
# )

# cursor = mdb.cursor()
# query = 'SELECT * FROM data'
# cursor.execute(query)

# with open('failed.txt','w+') as fp:
# 	for x in tqdm(cursor):
# 		try:
# 			rewrite(x)
# 		except:
# 			print(x[0],file=fp)

file = open('./../titles.txt', 'r')
def insert_title():
	for line in tqdm(file):
		entry_id = int(line.split('||')[0])
		title = line.split('||')[1].strip('\n').lstrip()
		entry = Entry.query.filter(Entry.id==entry_id).first()
		if entry:
			entry.title = title
			db.session.add(entry)
			db.session.commit()

if __name__ == '__main__':
	insert_title()
