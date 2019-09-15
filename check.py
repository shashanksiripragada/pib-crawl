import mysql.connector as mysql
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import time
import numpy as np
import langid
from lmdbcache import LMDBCacheContextManager
lmdbpath = "inserted"

langid.set_languages(['en','hi','ur','mr','te','ta','pa','bn','kn','or','gu','as','ml'])

def url_open(url):
    req = Request(url, headers=headers)
    web_byte = urlopen(req).read()
    web_page = web_byte.decode('utf-8')
    soup = BeautifulSoup(web_page, 'html.parser')
    return soup

headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
    'referrer': 'https://google.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    }

#cursor.execute("CREATE TABLE data (prid INT, text MEDIUMTEXT, date VARCHAR(255))")
'''
def insert(prid,text,date):
	query = "INSERT INTO data (prid, text, date) VALUES (%s, %s, %s)"
	values = (prid, text, date)
	cursor.execute(query, values)
	db.commit()
#insert(1,"test",None)
#print(cursor.rowcount, "record inserted")
'''



'''
def update(prid):
	day,year=0,0
	month,time,place='','',''
	output=[]	
	query = "SELECT text FROM data WHERE prid = %s"
	cursor.execute(query,(prid,))
	text = cursor.fetchall()
	if text!=[]:
		text = text[0][0]
		lang = langid.classify(text)[0]
		text = text.strip().split('\n')
		for t in text:
			b=t.strip()
			if b!='' and filt(b):
				output.append(b)
			if b!='' and (('PM' in b) or ('AM' in b)) and (':' in b) and ('by' in b) and ('PIB' in b):
				info=b.split(' ')
				l=len(info)
				day,month,year,time,place=info[0],info[1],info[2],info[3],info[l-1]		
		final='\n'.join(output)
		print(final)
		#insert(prid,day,month,year,time,place,lang,final)
		#print('inserted for prid:{}'.format(i))
		#cache(str(i), 'success')
'''
#upda
	



from webapp import db
from webapp.models import Entry

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
		#print(x)
		#print(x)
		# break
		try:
			rewrite(x)
		except:
			print(x[0],file=fp)



