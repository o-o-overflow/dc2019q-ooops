#!/usr/bin/env python

import sys
import os
import sqlite3
from twisted.web import proxy, http
from twisted.python import log
from twisted.python.compat import urllib_parse, urlquote

# CONFIG
BAD_WORD = "overflow"
DB_NAME = "/app/database.sqlite"
FILE_DIR = "./prox-internal"
PROXY_BASE = "/ooops/d35fs23hu73ds"
# end config

# Setup database connection
conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

def full_path_to_file(path):
    print(path)
    no_proto = path.split("://")[1]
    path_only = no_proto[no_proto.index("/"):]
    path_only = os.path.abspath(path_only)
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

class FilterProxyRequest(proxy.ProxyRequest):
    # Called when we get a request from a client

    def has_valid_creds(self):
        global GRADER_IP
        ip = self.getClientIP().encode('ascii')
        # Selenium can't handle proxy creds so just whitelist it by IP
        if ip in["localhost", "127.0.0.1", GRADER_IP]: return True

        return self.getHeader("Proxy-Authorization") == \
                "Basic T25seU9uZTpPdmVyZmxvdw==" # OnlyOne:Overflow

    def request_creds(self):
        self.setResponseCode(407)
        self.setHeader("Proxy-Authenticate", "Basic realm=\"Access to proxy site".encode("ascii"))
        self.write("Auth required".encode("ascii"))
        self.finish()




    def serve_internal(self, path):
        # Render internal page
        global PROXY_BASE, FILE_DIR
        # Swap PROXY_BASE prefix for FILE_DIR
        local_file=full_path_to_file(path).replace(PROXY_BASE, FILE_DIR)

        # If it's a POST, try parsing an unblock request
        if b'url' in self.args.keys():
            url = self.args[b'url'][0].decode("ascii")
            update_db(self.getClientIP().encode("ascii"), url)

        if os.path.isfile(local_file) and local_file.startswith(FILE_DIR):
            # If file exists in FILE_DIR, serve it
            ctype ="text/html"
            if "." in local_file:
                ext = local_file.split(".")[-1]
                if ext == "js": ctype = "script/javascript"
                if ext == "jpg": ctype = "image/jpeg"

            file_len = os.path.getsize(local_file)
            self.setResponseCode(200)
            self.setHeader("Content-Type", ctype.encode("ascii"))
            self.setHeader("Content-Length", str(file_len).encode("ascii"))

            for _bytes in read_bytes_from_file(local_file):
                self.write(_bytes)

            self.transport.write(b"\r\n")
            self.finish()
        else:
            self.setResponseCode(404)
            self.write("File not found\r\n".encode("ascii"))
            self.finish()

    def serve_blocked(self):
        path = PROXY_BASE +"/blocked.html"
        self.serve_internal(path)

    # Overload process for bugfixes AND to intercept request
    # For https see https://twistedmatrix.com/pipermail/twisted-python/2008-August/018227.html
    def process(self, args=None):
        if not self.has_valid_creds():
            self.request_creds()
            return None

        parsed = urllib_parse.urlparse(self.uri)
        protocol = parsed[0]
        host = parsed[1].decode('ascii')
        if protocol not in self.ports:
            self.setResponseCode(400)
            self.write("Unsupported protocol\r\n".encode("ascii"))
            self.finish()
            return None

        port = self.ports[protocol]
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
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
            self.serve_internal(dec_path)
        elif should_block(dec_path):
            # 2nd priority: blocked page
            self.serve_blocked()
        else: 
            # 3rd priority: regular page
            self.reactor.connectTCP(host, port, clientFactory)

class FilterProxy(proxy.Proxy):
    def requestFactory(self, *args):
        return FilterProxyRequest(*args)

class FilterProxyFactory(http.HTTPFactory):
    def buildProtocol(self, addr):
        protocol = FilterProxy()
        return protocol

if __name__ == '__main__':
    from twisted.internet import reactor
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
