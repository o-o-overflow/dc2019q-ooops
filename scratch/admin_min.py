#!/usr/bin/env python3

import sqlite3
import random
import time
import multiprocessing
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.proxy import Proxy, ProxyType
import os
import sys

INTERNAL="192.168.1.159:5000"

def do_request(driver, rid, url):
    global INTERNAL
    print("Start of do_request")

    # Avoid potential issues with files
    if not url.lower().startswith("http://") and not url.lower().startswith("https://"):
        print("Skipping request of malformed url {}".format(url))
        return False

    #s = time.time()
    #logger.info("Loading {} requested by {}".format(url, requested_by))
    internal_url = "http://{}/admin/view/{}".format(INTERNAL,rid)
    print("Loading {} indirectly via {}".format(url, internal_url))


    try:
        print("Get...")
        driver.get(internal_url)
        print("Got")
        print(driver.page_source)
        print("src")
    except TimeoutException:
        print("Timeout")
        return False

    try:
        print("Search for lnk")
        lnk = driver.find_element_by_id("lnk")
        print(lnk)
    except WebDriverException as e:
        print("Couldn't find lnk in page")
        print(e)
        return False

    # Click link and wait 2s
    print("Clicking...")
    lnk.click()
    print("Waiting...")
    driver.implicitly_wait(2)
    print("Source")
    print(driver.page_source)

    return True


PROXY_HOST="127.0.0.1"
PROXY_PORT=7239
os.environ['MOZ_HEADLESS'] = '1'
#FF_BIN = FirefoxBinary('/usr/bin/firefox', log_file=sys.stdout)
"""
def make_ff_driver():
    global PROXY_HOST, PROXY_PORT
    FF_BIN = FirefoxBinary('/usr/bin/firefox', log_file=sys.stdout)
    fp = webdriver.FirefoxProfile()
    fp.set_preference("network.proxy.type", 1)
    fp.set_preference("network.proxy.http",PROXY_HOST)
    fp.set_preference("network.proxy.http_port",PROXY_PORT)
    #fp.set_preference("network.proxy.ssl",PROXY_HOST)
    #fp.set_preference("network.proxy.ssl_port",PROXY_PORT)
    #fp.set_preference("http.response.timeout", 5)
    #fp.set_preference("dom.max_script_run_time", 5)
    fp.update_preferences()
    return webdriver.Firefox(firefox_profile=fp, firefox_binary=FF_BIN)

driver = make_ff_driver()
"""

FF_BIN = FirefoxBinary('/usr/bin/firefox', log_file=sys.stdout)
fp = webdriver.FirefoxProfile()
fp.set_preference("network.proxy.type", 1)
fp.set_preference("network.proxy.http",PROXY_HOST)
fp.set_preference("network.proxy.http_port",PROXY_PORT)
fp.set_preference("network.proxy.ssl",PROXY_HOST)
fp.set_preference("network.proxy.ssl_port",PROXY_PORT)
fp.set_preference("http.response.timeout", 5)
fp.set_preference("dom.max_script_run_time", 5)
fp.update_preferences()
driver = webdriver.Firefox(firefox_profile=fp, firefox_binary=FF_BIN)

try:
    print("Try 1")
    driver.get("http://overflow.blocked.com")
    driver.implicitly_wait(2)
    lnk = driver.find_element_by_id("lnk")
    lnk.click()

    driver.get("http://192.168.1.159:5000/admin/view/1")
    driver.implicitly_wait(5)
    lnk = driver.find_element_by_id("lnk")
    print(driver.page_source)
    lnk.click()
    print(driver.page_source)




    #internal_url = "http://192.168.1.159:5000/admin/view/{}".format(5)
    #driver.get(internal_url)
    
    #driver = webdriver.PhantomJS('/usr/bin/phantomjs')
    #rid = 5
    #url = "http://state.actor/log.php?v=5"
    #print(do_request(driver, rid, url))

finally:
    driver.quit()
