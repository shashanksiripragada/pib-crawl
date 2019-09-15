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

db = mysql.connect(
  host='localhost',
  user='root',
  database='pibscrape'
)

cursor = db.cursor()

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

def filt(text):
	flag=1
	garb = ['Posted On:','by PIB','ID:','/']
	for fil in garb:
		if fil in text:
			flag=0
	return flag

def insert(prid,day,month,year,time,place,lang,clean):
	query = "UPDATE data SET day = %s, month = %s, year = %s, time = %s, place = %s, lang = %s, clean = %s WHERE prid = %s"
	values = (day, month, year, time, place, lang, clean, prid)
	cursor.execute(query, values)
	db.commit()

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
		insert(prid,day,month,year,time,place,lang,final)
		print('inserted for prid:{}'.format(i))
		cache(str(i), 'success')



with LMDBCacheContextManager(lmdbpath+"error") as errorcache:
	with LMDBCacheContextManager(lmdbpath) as cache:
		for i in range(1483205,1584922):
			if (not cache.db.findkey(str(i))) and (not errorcache.db.findkey(str(i))):
				try:
					update(i)
				except Exception as e:
					print('failed to insert for prid:{}'.format(i),e)
					errorcache(str(i), e)
					pass



#ind=time[len(time)-2:len(time)]
#time=time[:len(time)-2]+':00'	
'''
out=[]
soup = url_open('https://pib.gov.in/PressReleasePage.aspx?PRID=1581820')
content = soup.find('div', {'id': 'PdfDiv'})
text = content.text.strip().split('\n')
for t in text:
	b=t.strip()
	if b!='':
		out.append(b)
	if b!='' and (('PM' in b) or ('AM' in b)):
		info=b.split(' ')
		l=len(info)
		day,month,year,time,place=info[0],info[1],info[2],info[3],info[l-1]
		print(day,month,year,time,place)

#print(date)
final='\n'.join(out)
#final=final.split('\n')
'''