from twisted.web import proxy, http
from twisted.internet import reactor
from twisted.python import log
import sys
import re
import ast
log.startLogging(sys.stdout)

PROXY_BASE = "/mgw"


def html(text):
    return """<!doctype html>
<html>
{}
</html>""".format(text)

def blocked(url):
    if "test" in url:
        return True


class MyProxy(proxy.Proxy):
    forceResp = False

    def respond(self, msg):
        m = html(msg)
        self.transport.write("HTTP/1.1 200 OK\r\nContent-Length: {}\r\nContent-Type: text/html\r\n\r\n{}".format(len(m), m).encode("utf-8"))
        #self.write(html(msg))
        self.transport.loseConnection()

    def dataReceived(self, data):
        method = re.search(b'^[A-Z]* [a-zA-Z]*\:\/\/([a-zA-z0-9\-.]*)\/([A-Za-z0-9\/\-\_\.]*) HTTP\/\d.\d', data)

        if not method or not method.groups(0) or not method.groups(1):
            print(repr(method))
            raise RuntimeError("Could not extract a URL/Path - FIXME")

        url = method.groups(0)[0].decode("utf-8")
        path = "/"+method.groups(0)[1].decode("utf-8")
        print("Path: {} url: {}".format(url, path))

        if path.startswith(PROXY_BASE):
            print("DEAD")
            self.forceResp = "Proxy this page"
            self.respond("Proxy<script>alert(1)</script>")
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
reactor.listenTCP(8080, factory)
reactor.run()
