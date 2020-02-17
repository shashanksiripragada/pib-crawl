from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import time
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions

# headers = {
#     'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 Safari/537.36',
#     'referrer': 'https://google.com',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
#     'Accept-Encoding': 'gzip, deflate, br',
#     'Accept-Language': 'en-US,en;q=0.9',
#     }


EXEC_PATH = "/home/shashank/Desktop/selenium-test/chromedriver"
options = Options()
#options.add_argument("--headless")
driver = webdriver.Chrome(options=options, executable_path=EXEC_PATH)
url = "https://pib.gov.in/PressReleasePage.aspx?PRID=1603145"

driver.get(url)
lang_list = driver.find_element_by_xpath("//div[@class='ReleaseLang']")
links = lang_list.find_elements_by_xpath("//a[contains(@href,'java')]")
length = len(links)

def get_id(index):
    lang_list = driver.find_element_by_xpath("//div[@class='ReleaseLang']")
    links = lang_list.find_elements_by_xpath("//a[contains(@href,'java')]")
    link = links[index]
    link.click()
    link_id = driver.find_element_by_xpath("//div[@class='releaseId']")
    _id = link_id.text
    close_btn = driver.find_element_by_xpath("//input[@name='btnClose']")
    close_btn.click()
    return _id

for index in range(length):
    link_id = get_id(index)    
    print(link_id)
    time.sleep(1)    
    #your_element = WebDriverWait(driver, 10, ignored_exceptions=ignored_exceptions)\
    #               .until(expected_conditions.presence_of_element_located((By.XPATH, "//a[contains(@id,'repLang_LinkButton')]")))
    #wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@id,'repLang_LinkButton')]")))
    #except StaleElementReferenceException as Exception:
