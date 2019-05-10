#!/usr/bin/env python

from twisted.web import proxy, http
import sys
from twisted.python import log
from twisted.python.compat import urllib_parse, urlquote

PROXY_PORT = 8090

class FilterProxyRequest(proxy.ProxyRequest):
    # Called when we get a request from a client

    # Overload process for bugfixes AND to intercept request
    # For https see https://twistedmatrix.com/pipermail/twisted-python/2008-August/018227.html
    def process(self):
        parsed = urllib_parse.urlparse(self.uri)
        protocol = parsed[0]
        host = parsed[1].decode('ascii')
        if protocol not in self.ports:
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

        if "overflow" not in host: # Unblocked, behave as normal
            self.reactor.connectTCP(host, port, clientFactory)
        else: #Blocked
            self.write("HTTP/1.1 200 OK\r\n\r\nBleh\r\n".encode("utf-8"))
            self.finish()

class FilterProxy(proxy.Proxy):
    def requestFactory(self, *args):
        return FilterProxyRequest(*args)

class FilterProxyFactory(http.HTTPFactory):
    def buildProtocol(self, addr):
        protocol = FilterProxy()
        return protocol


from twisted.internet import reactor
prox = FilterProxyFactory()
reactor.listenTCP(PROXY_PORT, prox)
reactor.run()
