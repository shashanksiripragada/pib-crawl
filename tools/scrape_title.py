import sys
sys.path.insert(1, '../')
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import time
import numpy as np
from webapp import db
from webapp.models import Entry
from tqdm import tqdm
import csv

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


def insert(entry_id, text):
    entry = Entry.query.filter(Entry.id==entry_id).first()
    if entry:
        entry.title = text
        db.session.add(entry)
        db.session.commit()
    

def scrape():
    fil = open('error.txt','a')
    for i in tqdm(range(1588466,1590000)):
        if not exists(i):
            try:
                soup = url_open('https://pib.gov.in/PressReleasePage.aspx?PRID={}'.format(i))
            except Exception as e:
                print(i,e)
                continue
            else:
                content = soup.find('div', {'class': 'MinistryNameSubhead text-center'})
                try:
                    title = content.text.strip()
                    if title != '':
                        insert(i, title)
                        print('release found with id:{} and inserted into db'.format(i))
                except Exception as e:
                    print(i,e,file=fil)
                    continue


if __name__ == '__main__':
    scrape()