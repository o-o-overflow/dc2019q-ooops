#!/usr/bin/env python3

import sqlite3
import random
import time
import multiprocessing
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.proxy import Proxy, ProxyType
from base64 import b64decode
import os
import sys

##### configuration ######
# Number of threads
NUM_THREADS = 1

# Number of requests to process in each thread
REQ_PER_THREAD = 1

# Time to allow for each request (note 2 requests per query)
TIMEOUT = 10 # TODO?

# Time to wait when there's nothing to do
NOTHING_WAIT = 5

# Sqlite database path
db_name = "/app/database.sqlite"
##########################


FORMAT = 'ADMIN: %(threadName)s: %(asctime)-10s %(message)s'
logging.basicConfig(level=logging.INFO,format=FORMAT)
logger = logging.getLogger(__name__)

os.environ['MOZ_HEADLESS'] = '1'
FF_BIN = FirefoxBinary('/usr/bin/firefox', log_file=sys.stdout)
def make_ff_driver():
    global PROXY_HOST, PROXY_PORT, FF_BIN
    fp = webdriver.FirefoxProfile()
    fp.set_preference("network.proxy.type", 1)
    fp.set_preference("network.proxy.http",PROXY_HOST)
    fp.set_preference("network.proxy.http_port",PROXY_PORT)
    fp.set_preference("network.proxy.ssl",PROXY_HOST)
    fp.set_preference("network.proxy.ssl_port",PROXY_PORT)
    fp.set_preference("http.response.timeout", 5)
    fp.set_preference("dom.max_script_run_time", 5)
    fp.set_preference("network.http.connection-timeout", 10);
    fp.set_preference("network.http.connection-retry-timeout", 10);
    fp.update_preferences()
    return webdriver.Firefox(firefox_profile=fp, firefox_binary=FF_BIN)

def do_request(driver, rid, url):
    """ 
    Actually load a page via the admin page via the proxy
    Returns bool indicating success
    """
    global INTERNAL, TIMEOUT, logger

    logger.debug("Start of do_request")

    # Avoid potential issues with files
    try:
        dec_url = b64decode(url).decode("utf-8")
    except Exception as e:
        print(e)
        return False

    if not dec_url.lower().startswith("http://") and not dec_url.lower().startswith("https://"):
        logger.warn("Skipping request of malformed url {}".format(dec_url))
        return False

    #s = time.time()
    #logger.info("Loading {} requested by {}".format(url, requested_by))
    internal_url = "http://{}/admin/view/{}".format(INTERNAL, rid)
    logger.info("Loading {} indirectly via {}".format(dec_url, internal_url))

    # First load internal page which contains link (to set referrer)
    # TODO: test timeouts
    #print("Load internal: {}".format(internal_url))
    driver.set_page_load_timeout(TIMEOUT)
    try:
        driver.get(internal_url)
    except TimeoutException:
        logger.warning("Timeout loading {}".format(internal_url))
        return False
    except UnexpectedAlertPresentException as e:
        logger.info("Saw alert: {}".format(e))

    #logger.info("INTERNAL PAGE: {}".format(driver.page_source))

    try:
        lnk = driver.find_element_by_id("lnk")
    except NoSuchElementException:
        logger.warning("Couldn't find lnk in page: {}".format(driver.page_source))
        return False

    try:
        lnk.click()
        driver.implicitly_wait(TIMEOUT)
    except UnexpectedAlertPresentException as e:
        logger.info("Saw alert: {}".format(e))

    #e = time.time()
    #print("\t Request took {:f} seconds".format(e-s))
    return True

def run_thread(thread_id):
    """
    Each thread will manage the newest [REQ_PER_THREAD] requests, selecting
    a maximum of 1 request per IP
    """
    global db_name, REQ_PER_THREAD, TIMEOUT, service_args, proxy_auth_token
    assert (thread_id > 3)

    driver = make_ff_driver()
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    try:
        while True:
            to_process = []

            # Select 10 IPs with the newest submissions and select their newest requests
            q = "UPDATE requests SET visited={:d} where rowid in (select max(ROWID) as rid from requests" \
                " where visited=0 group by ip order by ts DESC limit {:d});".format(thread_id, REQ_PER_THREAD)
            r = cur.execute(q)
            conn.commit()

            q2 = "select rowid, * from requests where visited={:d} order by ts DESC;".format(thread_id)
            r2 = cur.execute(q2)
            to_process = r2.fetchall()

            if not len(to_process):
                logging.info("No requests to process...")
                time.sleep(NOTHING_WAIT)

            # For each selected request, try to fetch the page
            # and update the rows in the DB accordingly
            successes = []
            errors = []
            for req in to_process:
                if do_request(driver, req[0], req[3]):
                    successes.append(req[0])
                else:
                    errors.append(req[0])

            if len(successes):
                q_s = "UPDATE requests set visited=1 where rowid in ({})".format(", ".join(map(str, successes)))
                r_s = cur.execute(q_s)
                conn.commit()

            if len(errors):
                q_e = "UPDATE requests set visited=2 where rowid in ({})".format(", ".join(map(str, errors)))
                r_e = cur.execute(q_e)
                conn.commit()
    finally:
        print("Shutting down Headless FF")
        driver.quit()

# DB has visited enum:
# 0 => To visit
# 1 => Visited
# 2 => error visiting
# x => pending for thread with ID x (note x > 2)


# Simple test. Looks like it can process about 20 requests per second for fast pages
"""
conn = sqlite3.connect(db_name)
cur = conn.cursor()
q = 'insert into requests VALUES("auto.ip", DateTime("now"), "http://state.actor/log.php?v=auto", 0);'
for _ in range(0, 10000):
    cur.execute(q)
conn.commit()
"""

if __name__ == '__main__':
    import sys
    assert(len(sys.argv) == 4), "Usage: ./admin.py [Internal-WWW public IP] [Internal-WWW Port] [Localhost's Proxy Port]"

    global INTERNAL, PROXY_HOST, PROXY_PORT
    # Public IP/port to connect to for internal-www
    INTERNAL = sys.argv[1]+":"+sys.argv[2]
    # Port to use for the proxy. Assumed to be running on localhost
    PROXY_PORT=int(sys.argv[3])

    # Host for the proxy
    PROXY_HOST = sys.argv[1]

    with ThreadPoolExecutor(max_workers=NUM_THREADS) as e:
        futures = []
        for _ in range(NUM_THREADS):
            thread_id = random.randint(3, 2**31)
            logger.info("Starting thread with ID {}".format(thread_id))
            futures.append(e.submit(run_thread, thread_id))

        for future in as_completed(futures):
            if future.exception():
                raise future.exception()
