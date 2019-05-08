#!/usr/bin/env python3

import sys
import re
import os
import sqlite3
import string
from urllib.parse import unquote
from twisted.web import proxy, http
from twisted.internet import reactor, ssl
from twisted.python import log

log.startLogging(sys.stdout)

# Configuration
PORT=7239
PROXY_BASE = "/ooops/d35fs23hu73ds"

# URLs containing this are blocked
BAD_WORD = "overflow"

# Ports other than these are blocked
ALLOWED_PORTS = [80, 443, 5000]

db_name = "../database.sqlite"

HTTP_REGEX=b'^([A-Z]*) ([a-zA-Z]*\:\/\/)?([a-zA-z0-9\-.]*)(:[\d]*)?(\/([A-Za-z0-9\/\-\_\.\;\%\=]*))?((\?([A-Za-z_0-9\'"!%&()\*+,-./:;=?@\\^_`{}|~\[\]])*)?)? HTTP\/\d.\d'

# End configuration

# Setup database connection
conn = sqlite3.connect(db_name)
cur = conn.cursor()


def update_db(user, url):
    global cur
    # Whitelist allowed characters to avoid SQLi
    safe_url = "".join([c for c in url if c in (string.ascii_letters + string.digits + ":/?.#=-_")])
    if len(safe_url):
        q = "INSERT into requests VALUES ('{ip}', {ts}, '{url}', 0);".format(ip=user, ts="DateTime('now')", url=safe_url)
        log.err("Inserting: {}".format(q))
        conn.execute(q)
        conn.commit()

def html(text):
    return """<!doctype html>
<html>
{}
</html>""".format(text)

def err(code, msg):
    return "HTTP/1.1 {code} {msg}\r\n\r\n{msg}\r\n".format(code=code, msg=msg).encode("utf-8")

def blocked(url, port, path):
    global BAD_WORD, ALLOWED_PORTS
    if BAD_WORD in url or port not in ALLOWED_PORTS:
        if PROXY_BASE not in path: # Don't block internal pages, even on blocked sites
            return True
    return False

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

    def request_creds(self):
        # Ask for credentials
        self.transport.write("HTTP/1.1 407 Proxy Authentication Required\r\nProxy-Authenticate: Basic realm=\"Access to proxy site\"\r\n\r\n{}".encode("utf-8"))
        self.transport.loseConnection()

    def has_valid_creds(self, data):
        data = data.decode("utf-8", "ignore")
        if "Proxy-Authorization: " not in data:
            self.request_creds()
            return False
        postauth = data.split("Proxy-Authorization: ")[1]
        if "\r\n" not in postauth:
            print("Malformed proxy auth")
            return False

        auth_token = postauth.split("\n")[0].strip()
        if auth_token=="Basic T25seU9uZTpPdmVyZmxvdw==": # OnlyOne:Overflow
            return True
        else:
            self.request_creds()
            return False


    def dataReceived(self, data):
        """
        Client has send us a request, try to connect to it
        """
        global HTTP_REGEX
        try:
            return self._dataReceived(data)
        except Exception as e:
            print("Exception:" + str(e))
            self.transport.loseConnection()
            raise e
            return False


    def _dataReceived(self, data):
        #dec = data.decode("utf-8", "ignore")
        #print(dec)

        if not self.has_valid_creds(data):
            print("Invalid creds\n\n")
            self.transport.loseConnection()
            return False

        method = re.search(HTTP_REGEX, data)

        if not method or not method.groups(0) or not method.groups(1):
            print("Malformed request")
            self.transport.write(err(400, "Bad Request"))
            self.transport.loseConnection()
            return False
    
        meth  = method.groups(0)[0].decode("utf-8")

        # Don't support HTTPS - TODO add support
        if meth == "CONNECT":
            print("Ignoring HTTPS connect")
            self.transport.loseConnection()
            return False

        proto = method.groups(0)[1].decode("utf-8") # can be blank, or HTTP://, etc
        if not proto.startswith("http") or not proto.endswith("://"):
            print("Fail: bad proto")
            self.transport.write(err(400, "Bad Request"))
            self.transport.loseConnection()
            return

        url   = method.groups(0)[2].decode("utf-8", "ignore") # Includes subdomains
        port  = method.groups(0)[3] # Can be blank
        path  = method.groups(1)[4].decode("utf-8", "ignore")
        query = method.groups(0)[6].decode("utf-8", "ignore")

        user = self.transport.getPeer()
        user_ip = user.host
        log.err("Request from {}. URL: {}. Port: {}. Query: {}".format(user_ip, url, port, query))

        # Our headless browser is making a lot if these requests, just drop
        if url == "getpocket.cdn.mozilla.net":
            print("Dropping request to Firefox Pocket")
            self.transport.loseConnection()
            return False

        if port:
            port = int(port[1:]) # Trim leading ":"
        else:
            port=80 # Default is 80

        if query is not None: query = query[1:]

        if blocked(url, port, path): # Update path so we'll respond with internal file blocked.html
            print("URL blocked, update path to...")
            path = PROXY_BASE + "/blocked.html"
            print(path)

        path = os.path.abspath(path)
        if path.startswith(PROXY_BASE):
            local_file = "./prox-internal" + path.split(PROXY_BASE)[1] # Skip past proxy base
            if ".." in local_file: 
                self.transport.loseConnection()
                return

            if meth == "GET" or meth == "POST": # Load page if exists on get or post
                if meth == "POST": # For post, try parsing an unblock request
                    lines = data.decode("utf-8", "ignore").split("\r\n")
                    url=None
                    for line in lines:
                        if "url=" in line and "reason=" in line: # Found it
                            urldata = line.split("url=")[1]
                            try:
                                url=unquote(urldata.split("&")[0])
                            except:
                                print("Warning: Couldn't parse postdata line: {}".format(urldata))
                    if url:
                        update_db(user_ip, url)
                    else:
                        print("Warning: Couldn't parse posted data url")

                # Respond with raw file for get and post
                if os.path.isfile(local_file): # Ignore directories
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
                    self.transport.loseConnection()
                    return False

                else:

                    self.transport.write("HTTP/1.1 404 File not Found\r\n\r\nPage not found\r\n".encode("utf-8"))
                    self.transport.loseConnection()
                    return False
            else:
                self.transport.write("HTTP/1.1 405 Method not Allowed\r\n\r\nMethod not Allowed\r\n".encode("utf-8"))
                self.transport.loseConnection()
                return True

        data = re.sub(b'Accept-Encoding: [a-z, ]*', b'Accept-Encoding: identity', data)
        return proxy.Proxy.dataReceived(self, data)
    
    def write(self, data):
        if data:
            #print("\nServer response:\n{}".format(data.decode("utf-8")))
            self.transport.write(data)
        if self.transport:
            self.transport.loseConnection()

class ProxyFactory(http.HTTPFactory):
    protocol=MyProxy

factory = ProxyFactory()
reactor.listenTCP(PORT, factory)

"""
# TODO: SSL
reactor.listenSSL(PORT, factory,
        ssl.DefaultOpenSSLContextFactory(
            'cert/ca.key', 'cert/ca.crt'))
"""
reactor.run()
