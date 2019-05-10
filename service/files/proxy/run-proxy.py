#!/usr/bin/env python

import sys
import os
import sqlite3
import uuid # TODO: use for DB keys
import string
from captcha.image import ImageCaptcha
from random import choice, randint
from twisted.web import proxy, http
from twisted.python import log
from twisted.internet import reactor, ssl
from twisted.python.compat import urllib_parse, urlquote
from OpenSSL import SSL as OSSL

# CONFIG
BAD_WORD = "overflow"
PROXY_BASE = "/ooops/d35fs23hu73ds"
CAPTCHA_LEN = 5

# TODO: These paths are for docker
DB_NAME = "/app/database.sqlite"
FILE_DIR = "/app/proxy/prox-internal"

# And these paths are for local debugging
#FILE_DIR = "prox-internal"
#DB_NAME = "database.sqlite"

# END CONFIG

# Global imageCaptcha object
imageCaptcha = ImageCaptcha(fonts=['/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'])

# Setup database connection
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

def full_path_to_file(path):
    if "://" in path:
        path = path.split("://")[1]
    if "/" in path:
        path_only = path[path.index("/"):] # Trim after first /
        path_only = os.path.abspath(path_only)
    else:
        path_only = "/"

    return path_only

def is_internal_page(path):
    # Determine if a page is internal (prefixed with PROXY_BASE)
    global PROXY_BASE
    return full_path_to_file(path).startswith(PROXY_BASE)

def should_block(full_path):
    global BAD_WORD
    return BAD_WORD in full_path

def read_bytes_from_file(file, chunk_size = 2048):
    with open(file, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if chunk:
                yield chunk
            else:
                break

def update_db(user, url):
    global cur
    # B64 encode data. Probably overkill?
    q = "INSERT into requests VALUES (?, DateTime('now'), ?, 0);"
    log.err("Inserting: {}".format(q))
    conn.execute(q, (user, url.encode("ascii")))
    conn.commit()

def make_captcha(c_len=5):
    global imageCaptcha
# Write [junk].png and [junk].txt where the txt contains the answer
    captcha_chars = string.ascii_letters+string.digits
    ans   = ''.join(choice(captcha_chars) for i in range(c_len))
    fname = ''.join(choice(captcha_chars) for i in range(c_len))
    ans_fname = fname+".txt"
    fname += ".png"

    imageCaptcha.write(ans, os.path.join(FILE_DIR, 'captchas', fname))
    with open(os.path.join(FILE_DIR, 'captchas', ans_fname), "w") as f:
        f.write(ans)

    return (os.path.join(PROXY_BASE, 'captchas', fname), fname)

def check_captcha(imgname, guess):
    fname = os.path.abspath(os.path.join(FILE_DIR, 'captchas', imgname))
    ansname = fname.replace(".png", ".txt")
    print(fname, ansname)
    if ".." in imgname or FILE_DIR not in fname:
        return False

    if not os.path.isfile(fname) or not os.path.isfile(ansname):
        return False

    ans = open(ansname).read()
    os.remove(fname)
    os.remove(ansname)

    return guess == ans

class MySSLContext(ssl.DefaultOpenSSLContextFactory):

   def __init__(self, *args, **kw):
        #kw['sslmethod'] = OSSL.TLSv1_METHOD
        #args['privateKeyFileName'] = 'cert/ca.key'
        #args['certificateFileName'] = 'cert/ca.crt'
        ssl.DefaultOpenSSLContextFactory.__init__(self,
         "cert/ca.key", "cert/ca.crt", sslmethod=OSSL.TLSv1_1_METHOD)

   """
   def getContext(self):
       ctx = OSSL.Context(OSSL.TLSv1_1_METHOD)
       ctx.use_certificate_file('cert/ca.crt')
       ctx.use_privatekey_file('cert/ca.key')
       return ctx
   """

class MySSLContext2(ssl.ContextFactory):
   def getContext(self):
       ctx = OSSL.Context(OSSL.TLSv1_1_METHOD)
       ctx.use_certificate_file('cert/ca.crt')
       ctx.use_privatekey_file('cert/ca.key')
       return ctx

class FilterProxyRequest(proxy.ProxyRequest):
    # Called when we get a request from a client

    def has_valid_creds(self):
        global GRADER_IP
        ip = self.getClientIP().encode('ascii')
        # Selenium can't handle proxy creds so just whitelist it by IP
        if ip in["localhost", "127.0.0.1", GRADER_IP]:
            #log.msg("Request from grader/localhost. No creds required")
            return True

        return self.getHeader("Proxy-Authorization") == \
                "Basic T25seU9uZTpPdmVyZmxvdw==" # OnlyOne:Overflow

    def request_creds(self):
        self.setResponseCode(407)
        self.setHeader("Proxy-Authenticate", "Basic realm=\"Access to proxy site".encode("ascii"))
        self.write("Auth required".encode("ascii"))
        self.finish()


    def serve_internal(self, path, doSSL):
        # Render internal page
        global PROXY_BASE, FILE_DIR
        # Swap PROXY_BASE prefix for FILE_DIR
        local_file=full_path_to_file(path).replace(PROXY_BASE, FILE_DIR)

        msg = "" # Messages to show on page

        # Try parsing an unblock request
        if self.method.upper() == b'POST':
            msg = "Missing arguments" # Default for a post

        if b'url' in self.args and b'captcha_guess' in self.args and \
            b'captcha_id' in self.args:

            captcha_guess = self.args[b'captcha_guess'][0].decode("ascii")
            captcha_id = self.args[b'captcha_id'][0].decode("ascii")

            if check_captcha(captcha_id, captcha_guess):
                msg = "Request submitted"
                url = self.args[b'url'][0].decode("ascii")
                update_db(self.getClientIP().encode("ascii"), url)
            else:
                msg = "Invalid captcha"

        if os.path.isfile(local_file) and local_file.startswith(FILE_DIR):
            # If file exists in FILE_DIR, serve it
            ctype ="text/html"
            if "." in local_file:
                ext = local_file.split(".")[-1]
                if ext == "js": ctype = "script/javascript"
                if ext == "jpg": ctype = "image/jpeg"
                if ext == "png": ctype = "image/png"

            file_len = os.path.getsize(local_file)
            self.setResponseCode(200)
            self.setHeader("Content-Type", ctype.encode("ascii"))
            self.setHeader("Content-Length", str(file_len).encode("ascii"))

            if ctype == "text/html": # Small file, safe to parse all at once
                with open (local_file) as f:
                    _file_contents = f.read()
                    if "{captcha_" in _file_contents:
                        # Dynamically rewrite captcha template tags
                        c_path, c_id = make_captcha()
                        _file_contents = _file_contents.replace("{captcha_url}", c_path)
                        _file_contents = _file_contents.replace("{captcha_id}", c_id)

                    if "{msg}" in _file_contents:
                        _file_contents = _file_contents.replace("{msg}", msg)

                    self.write(_file_contents.encode("ascii"))

            else: # Binray, just send raw bytes
                for _bytes in read_bytes_from_file(local_file):
                    self.write(_bytes)

            self.transport.write(b"\r\n")
            self.finish()
        else:
            self.setResponseCode(404)
            self.write("File not found\r\n".encode("ascii"))
            self.finish()

    def serve_blocked(self, doSSL):
        path = PROXY_BASE +"/blocked.html"
        self.serve_internal(path, doSSL)

    protocols = {b'http': proxy.ProxyClientFactory, b'https': proxy.ProxyClientFactory}
    ports = {b'http': 80, b'https': 443}

    # Overload process for bugfixes AND to intercept request
    # https logic from
    # https://twistedmatrix.com/pipermail/twisted-python/2008-August/018227.html
    def process(self, args=None):
        if not self.has_valid_creds():
            self.request_creds()
            return None


        parsed = urllib_parse.urlparse(self.uri)
        protocol = parsed[0]
        host = parsed[1].decode('ascii')

        port = 80
        if protocol != b'':
            port = self.ports[protocol]
        if ':' in host:
            host, port = host.split(':')
            port = int(port)

        doSSL = False
        if self.method.upper() == b"CONNECT": # TODO: finish HTTPS support
            #self.setResponseCode(200)
            self.transport.write("HTTP/1.1 200 Connection established\r\nConnection: close\n\n".encode("ascii"))
            self.transport.startTLS(MySSLContext2())
            protocol = b"https"
            self.host = parsed.scheme
            #self.transport.write("HTTPS unsupported\r\n".encode("ascii"))
            self.finish()
            return
        else:
            if self.isSecure():
                headers = self.getAllHeaders().copy()
                host = headers["host"]
                protocol = b"https"
                doSSL = True


        if protocol not in self.ports:
            self.setResponseCode(400)
            self.write("Unsupported protocol\r\n".encode("ascii"))
            self.finish()
            return None

        rest = urllib_parse.urlunparse((b'', b'') + parsed[2:])
        if not rest:
            rest = rest + b'/'
        if protocol not in self.protocols:
            self.setResponseCode(400)
            self.write("Unsupported protocol\r\n".encode("ascii"))
            self.finish()
            return None

        class_ = self.protocols[protocol]
        headers = self.getAllHeaders().copy()
        if b'host' not in headers:
            headers[b'host'] = host.encode('ascii')

        # Add x-forwarded-for
        headers[b'X-Forwarded-For'] = self.getClientIP().encode('ascii')

        self.content.seek(0, 0)
        s = self.content.read()
        clientFactory = class_(self.method, rest, self.clientproto, headers,
                               s, self)

        #print("About to connect upstream to {}:{}".format(host, port))
        #print("Headers for upstream: {}".format(headers))

        dec_path = self.path.decode("ascii", "ignore")
        if is_internal_page(dec_path):
            # 1st priority: internal pages
            self.serve_internal(dec_path, doSSL)
        elif should_block(dec_path):
            # 2nd priority: blocked page
            self.serve_blocked(doSSL)
        else: 
            # 3rd priority: regular page
            if doSSL:
                print("Trying connect ssl to {} on {}".format(host, port))
                self.reactor.connectSSL(host, port, clientFactory,
                    ssl.ClientContextFactory())
            else:
                self.reactor.connectTCP(host, port, clientFactory)

class FilterProxy(proxy.Proxy):
    def requestFactory(self, *args):
        return FilterProxyRequest(*args)

class FilterProxyFactory(http.HTTPFactory):
    def buildProtocol(self, addr):
        protocol = FilterProxy()
        return protocol

assert(len(sys.argv) == 3), "Usage: ./run-proxy.py [Grader IP] [Port]"

global GRADER_IP, PORT
# GRADER_IP used to allow passwordless connections from admin
# because selenium can't handle proxies with passwords :(
GRADER_IP = sys.argv[1]
# Port to listen on
PORT = int(sys.argv[2])

prox = FilterProxyFactory()
reactor.listenTCP(PORT, prox)
"""
# TODO: SSL
reactor.listenSSL(PORT, factory,
        ssl.DefaultOpenSSLContextFactory(
            'cert/ca.key', 'cert/ca.crt'))
"""
reactor.run()
