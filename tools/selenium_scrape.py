from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

import os

from lmdbcache import LMDBCacheContextManager

RETRY = False
HEADLESS = False

PREFIXURL = "https://pib.gov.in/PressReleasePage.aspx?PRID="

class element_exists(object):
    """
    Checking that if element is clickable
    """

    def __init__(self, elem):
        self.elem = elem

    def __call__(self, driver):
        try:
            wait = WebDriverWait(driver, 0.5)
            wait.until(EC.elementToBeClickable(self.elem))
            self.elem.click()
            modaldialog = driver.find_element_by_xpath("""//*[@id="P_CategoryManagement"]""")
            releaseiddiv = modaldialog.find_element_by_class_name("releaseId")
            textdata = releaseiddiv.text
            iddata = textdata.split(": ")[1][:-1]
            closebutton = driver.find_element_by_id("btnClose")
            closebutton.click()
            return iddata
        except Exception as e:
            print(e)
            return False

class SeleniumCrawler():

    def __init__(self, driver):
        self.driver = driver

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.driver.close()
        self.driver.quit()

    def get_data(self):
        """
        Extract links
        """
        links = []
        otherlangs_div = self.driver.find_element_by_xpath("""//*[@id="form1"]/div[3]/div[2]/div[7]""")
        for langs in otherlangs_div.find_elements_by_tag_name('a'):
            try:
                wait = WebDriverWait(self.driver, 0.5)
                textdata = wait.until(element_exists(langs))
                links.append(textdata)
            except Exception as e:
                print(e)
        return links

    def get_links(self, urlid):
        """
        Get urls here using selenium
        """
        data = None
        newurl = PREFIXURL + str(urlid)
        try:
            self.driver.get(newurl)
            data = self.get_data()

        except Exception as e:
            print(e)
            pass

        print(urlid, data)
        return data


if __name__ == "__main__":

    options = Options()
    if HEADLESS:
        options.add_argument("--headless")
    EXEC_PATH = "/home/scorpio/ADA_DATA/en_te_newscrawler/chromedriver"
    driver = webdriver.Chrome(
        chrome_options=options, executable_path=EXEC_PATH)

    lmdbpath = "linkmatrixcache"
    errorcachepath = "errorcache"
    emptycachepath = "emptycache"

    with LMDBCacheContextManager(errorcachepath) as errorcache:
        with LMDBCacheContextManager(lmdbpath) as cache:
            with LMDBCacheContextManager(emptycachepath) as emptycache:
                with SeleniumCrawler(driver) as crawler:
                    for i in range(1483205,1584922):
                        if not (cache.db.findkey(str(i)) and emptycache.db.findkey(str(i))):
                            data = crawler.get_links(i)
                            if data==None:
                                errorcache(str(i), [])
                            elif len(data) == 0:
                                emptycache(str(i), [])
                            else:
                                cache(str(i), data)