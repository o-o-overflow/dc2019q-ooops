#!/usr/bin/env python3

from twisted.web import proxy, http
from twisted.internet import reactor, ssl
from twisted.python import log
import sys
import re
import os
log.startLogging(sys.stdout)

# TODO add auth, remove port

PORT=7239
PROXY_BASE = "/prox-internal/de5fs23hu73ds"


def html(text):
    return """<!doctype html>
<html>
{}
</html>""".format(text)

def blocked(url, path):
    if "test" in url and PROXY_BASE not in path: # Don't block internal pages, even on blocked sites
        return True
    return False

BAD_URLS = ["127.0.0.1", "127.1", "localhost"]

def read_bytes_from_file(file, chunk_size = 2048):
    with open(file, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            
            if chunk:
                    yield chunk
            else:
                break

class MyProxy(proxy.Proxy):
    def respond(self, msg, ctype="text/html"):
        m = html(msg)
        self.transport.write("HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type: {}\r\n\r\n{}".format(len(m), m, ctype).encode("utf-8"))
        #self.write(html(msg))
        self.transport.loseConnection()

    def has_valid_creds(self, data):
        data = data.decode("utf-8", "ignore")
        if "Proxy-Authorization: " not in data: return False
        postauth = data.split("Proxy-Authorization: ")[1]
        if "\r\n" not in postauth: return False
        auth_token = postauth.split("\n")[0].strip()
        return auth_token=="Basic dXNlcjpwYXNz" # user:pass

        # No valid creds, ask for them
        self.transport.write("HTTP/1.1 407 Proxy Authentication Required\r\nProxy-Authenticate: Basic realm=\"Access to proxy site\"\r\n\r\n{}".encode("utf-8"))
        self.transport.loseConnection()
        return False

    def dataReceived(self, data):
        if not self.has_valid_creds(data): return False

        method = re.search(b'^([A-Z]*) ([a-zA-Z]*\:\/\/)?([a-zA-z0-9\-.]*)(:[\d]*)?(\/([A-Za-z0-9\/\-\_\.\;\%\=]*))?((\?([A-Za-z0-9%=\\\(\)])*)?)? HTTP\/\d.\d', data)

        if not method or not method.groups(0) or not method.groups(1):
            print(data.decode("utf-8").split("\r\n")[0])
            raise RuntimeError("Could not extract a URL/Path - FIXME") # TODO needs work here
        meth  = method.groups(0)[0].decode("utf-8")

        # Don't support HTTPS - TODO add support
        if meth == "CONNECT":
            #print("Ignoring HTTPS connect")
            self.transport.loseConnection()
            return

        proto = method.groups(0)[1].decode("utf-8") # can be blank, or HTTP://, etc
        if not proto.startswith("http") or not proto.endswith("://"):
            print("Fail: bad proto")
            self.transport.loseConnection()
            return

        url   = method.groups(0)[2].decode("utf-8") # Includes subdomains
        port  = method.groups(0)[3] # Can be blank
        path  = method.groups(1)[4].decode("utf-8")
        query = method.groups(0)[6].decode("utf-8")

        if query is not None: query = query[1:]

        if url in BAD_URLS: # Block connecting to local ports? Not great, but it's something
            self.transport.loseConnection()
            return

        if blocked(url, path): # Update path so we'll respond with internal file blocked.html
            print("URL blocked, update path to...")
            path = PROXY_BASE + "/blocked.html"
            print(path)

        path = os.path.abspath(path)
        if path.startswith(PROXY_BASE):
            local_file = "./prox-internal" + path.split(PROXY_BASE)[1] # Skip past proxy base
            if ".." in local_file: 
                self.transport.loseConnection()
                return

            # Respond with raw file
            if os.path.exists(local_file):
                ctype ="text/html"
                if "." in local_file:
                    ext = local_file.split(".")[-1]
                    if ext == "js": ctype = "script/javascript"
                    if ext == "jpg": ctype = "image/jpeg"

                file_len = os.path.getsize(local_file)
                self.transport.write("HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type: {}\r\n\n".format(file_len, ctype).encode("utf-8"))

                self.setRawMode()
                for _bytes in read_bytes_from_file(local_file):
                    self.transport.write(_bytes)

                self.transport.write(b"\r\\n")
                self.setLineMode()
                self.transport.loseConnection() # Not sure why this has to happen here

            else:

                self.transport.write("HTTP/1.1 404 File not Found\r\n\r\nPage not found\r\n".encode("utf-8"))
                self.transport.loseConnection() # Not sure why this has to happen here

        data = re.sub(b'Accept-Encoding: [a-z, ]*', b'Accept-Encoding: identity', data)
        return proxy.Proxy.dataReceived(self, data)
    
    def write(self, data):
        if data:
            print("\nServer response:\n{}".format(data.decode("utf-8")))
            self.transport.write(data)
        self.transport.loseConnection()

class ProxyFactory(http.HTTPFactory):
    protocol=MyProxy

factory = ProxyFactory()
reactor.listenTCP(PORT, factory)

"""
# TODO run over https
reactor.listenSSL(PORT, factory,
        ssl.DefaultOpenSSLContextFactory(
            'cert/ca.key', 'cert/ca.crt'))
"""
reactor.run()
