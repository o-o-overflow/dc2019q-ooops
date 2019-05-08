#!/usr/bin/env python3

import sqlite3
import random
import time
import multiprocessing
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from base64 import b64encode

##### configuration ######
# Public IP/port to connect to for internal-www
INTERNAL="192.168.1.159:5000"

# Number of threads
NUM_THREADS = 10

# Number of requests to process in each thread
REQ_PER_THREAD = 10

# Time to allow for each request (note 2 requests per query)
TIMEOUT = 3

# Time to wait when there's nothing to do
NOTHING_WAIT = 5

# Sqlite database path
db_name = "../database.sqlite"

# Proxy config
service_args = [
    '--proxy=127.0.0.1:7239',
    '--proxy-type=http',
]
# Proxy credentials
proxy_creds = b"OnlyOne:Overflow"
proxy_auth_token = "Basic " + b64encode(proxy_creds).decode("utf-8")
##########################


FORMAT = '%(threadName)s: %(asctime)-10s %(message)s'
#logging.basicConfig(filename='admin.log',level=logging.DEBUG,format=FORMAT)
logging.basicConfig(level=logging.INFO,format=FORMAT)
logger = logging.getLogger(__name__)

def do_request(driver, rid, url):
    """ 
    Actually load a page via the admin page via the proxy
    Returns bool indicating success
    """
    global INTERNAL, TIMEOUT, logger

    logger.debug("Start of do_request")

    # Avoid potential issues with files
    if not url.lower().startswith("http://") and not url.lower().startswith("https://"):
        logger.warn("Skipping request of malformed url {}".format(url))
        return False

    #s = time.time()
    #logger.info("Loading {} requested by {}".format(url, requested_by))
    internal_url = "http:/{}/admin/view/{}".format(INTERNAL, rid)
    logger.info("Loading {} indirectly via {}".format(url, internal_url))

    # First load internal page which contains link (to set referrer)
    #driver.set_page_load_timeout(TIMEOUT)
    # TODO: doesn't timeout
    try:
        driver.get(internal_url)
    except TimeoutException:
        logger.warning("Timeout")
        return False

    try:
        lnk = driver.find_element_by_id("lnk")
    except WebDriverException as e:
        logger.warning("Couldn't find lnk in page: {}".format(driver.page_source))
        return False

    lnk.click()
    driver.implicitly_wait(TIMEOUT)

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

    caps = DesiredCapabilities.PHANTOMJS
    caps['phantomjs.page.customHeaders.Proxy-Authorization'] = proxy_auth_token

    driver = webdriver.PhantomJS('/usr/bin/phantomjs', service_args=service_args,
                                    desired_capabilities=caps)

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
                #logging.info("No requests to process...")
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
        print("Shutting down PhantomJS")
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

with ThreadPoolExecutor(max_workers=NUM_THREADS) as e:
    futures = []
    for _ in range(NUM_THREADS):
        thread_id = random.randint(3, 2**31)
        logger.info("Starting thread with ID {}".format(thread_id))
        futures.append(e.submit(run_thread, thread_id))

    for future in as_completed(futures):
        if future.exception():
            raise future.exception()
