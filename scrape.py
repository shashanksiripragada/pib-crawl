from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import time
import numpy as np

delays = [5, 4, 6, 2, 1, 3]

visited=[]

headers = {
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
    'referrer': 'https://google.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    }

def url_open(url):
    req = Request(url, headers=headers)
    web_byte = urlopen(req).read()
    web_page = web_byte.decode('utf-8')
    soup = BeautifulSoup(web_page, 'html.parser')
    return soup


for i in range(1479570,1590000):
	if i not in visited:
		delay = np.random.choice(delays)
		time.sleep(delay)
		soup = url_open('https://pib.gov.in/PressReleasePage.aspx?PRID={}'.format(i))
		visited.append(i)
		content = soup.find('div', {'id': 'PdfDiv'})
		text = content.text.strip()
		if(text != "Posted On:"):
			out=open('{}.txt'.format(i),'w')
			out.write(text)
			out.close()
		else:
			print('empty release found with id:{} found'.format(i))


'''
for i in range(1450000,1600000):
	try:
		soup=url_open('https://pib.gov.in/PressReleasePage.aspx?PRID={}'.format(i))		
	except:
		print('no release found with id:{} found'.format(i))
	else:
		paragraph=soup.find('div', {'id': 'PdfDiv'})
		if(paragraph!="Posted On:"):
			#print('empty release found with id:{} found'.format(i))
		#else:
			out=open('{}.txt'.format(i),'w')
			out.write(paragraph.text.strip())
			out.close()
'''

'''
soup=url_open('https://pib.gov.in/PressReleasePage.aspx?PRID=1350000')

#print(soup.text)

paragraph=soup.find('div', {'id': 'PdfDiv'})
txt=paragraph.text.strip()
print(txt)
out.write(txt)
'''