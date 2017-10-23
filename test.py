from twisted.web import proxy, http
from twisted.internet import reactor
from twisted.python import log
import sys
import re
import ast
log.startLogging(sys.stdout)

PROXY_BASE = "/mwg"


def html(text):
    return """<!doctype html>
<html>
{}
</html>""".format(text)

def blocked(url):
    if "test" in url:
        return True

with open("blocked.html", "r") as f:
    PROXY_PAGE = f.read()

BAD_URLS = ["127.0.0.1", "127.1", "localhost"]

class MyProxy(proxy.Proxy):
    forceResp = False

    def respond(self, msg):
        m = html(msg)
        self.transport.write("HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type: text/html\r\n\r\n{}".format(len(m), m).encode("utf-8"))
        #self.write(html(msg))
        self.transport.loseConnection()

    def dataReceived(self, data):
        method = re.search(b'^([A-Z]*) ([a-zA-Z]*\:\/\/)?([a-zA-z0-9\-.]*)(:[\d]*)?(\/([A-Za-z0-9\/\-\_\.\;\%\=]*))?((\?([A-Za-z0-9_\:\\.\-\&\=\%])*)?)? HTTP\/\d.\d', data)

        if not method or not method.groups(0) or not method.groups(1):
            print(repr(data))
            raise RuntimeError("Could not extract a URL/Path - FIXME")

        #print(method.groups())
        meth  = method.groups(0)[0].decode("utf-8")

        # Don't support HTTPS - TODO - send back an error?
        if meth == "CONNECT":
            print("Ignoring connect")
            self.transport.loseConnection()
            return

        proto = method.groups(0)[1].decode("utf-8") # can be blank, or HTTP://, etc
        url   = method.groups(0)[2].decode("utf-8") # Includes subdomains
        port  = method.groups(0)[3] # Can be blank
        path  = method.groups(1)[4].decode("utf-8")
        query = method.groups(0)[6].decode("utf-8")

        if query is not None: query = query[1:]

        if url in BAD_URLS: # Don't proxy local ports to the internet, not fully secure, but a little bit helps?
            self.transport.loseConnection()
            return

        if path.startswith(PROXY_BASE):
            print("Proxy this request")
            self.forceResp = "Proxy this page"
            self.respond(PROXY_PAGE)
            #return None

        if blocked(url):
            self.forceResp = "Blocked"
            self.respond("Blocked")
            #return None

        data = re.sub(b'Accept-Encoding: [a-z, ]*', b'Accept-Encoding: identity', data)

        print("\nClient req:\n{}".format(data.decode("utf-8")))
        return proxy.Proxy.dataReceived(self, data)
    
    def write(self, data):
        if self.forceResp:
            print("Sending custom resp")
            self.transport.write(self.forceResp.encode("utf-8"))
            self.transport.loseConnection()
        elif data:
            #print("\nServer response:\n{}".format(data.decode("utf-8")))
            self.transport.write(data)

class ProxyFactory(http.HTTPFactory):
    protocol=MyProxy

factory = ProxyFactory()
reactor.listenTCP(7239, factory)
reactor.run()
