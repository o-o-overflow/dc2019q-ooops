#!/usr/bin/env python

from twisted.web import proxy, http
import sys
from twisted.python import log

PROXY_PORT = 8090

class FilterProxyClient(proxy.ProxyClient):
    def handleHeader(self, key, value):
        print("Handle response header {}={}".format(key, value))
        proxy.ProxyClient.handleHeader(self, key, value)

    """
    def handleResponsePart(self, data):
        proxy.ProxyClient.handleResponsePart(self, data)

    def handleResponseEnd(self):
        proxy.ProxyClient.handleResponseEnd(self)
    """

class FilterProxyFactory(proxy.ProxyClientFactory):
    def buildProtocol(self, addr):
        client = proxy.ProxyClientFactory.buildProtocol(self, addr)
        # upgrade proxy.proxyClient object to FilterProxyClient
        client.__class__ = FilterProxyClient
        return client

class FilterProxyRequest(proxy.ProxyRequest):
    protocols = {b'http': FilterProxyFactory}
    # How is this different from a self.protocols= after init?

    def __init__(self,*args):
        super(FilterProxyRequest, self).__init__(*args)

    """
    def process(self):
        try:
            proxy.ProxyRequest.process(self)
            print("Request for: {}".format(self.host))
        except KeyError: # Unsupported protocols
            # TODO: send a message back to the browser
            return None
    """

    def process(self):
        from twisted.python.compat import urllib_parse, urlquote
        parsed = urllib_parse.urlparse(self.uri)
        protocol = parsed[0]
        host = parsed[1].decode('ascii')
        if protocol not in self.ports:
            if protocol != b'':
                print("TODO: ERROR, unknown port: {}".format(protocol))
            return None

        port = self.ports[protocol]
        if ':' in host:
            host, port = host.split(':')
            port = int(port)
        rest = urllib_parse.urlunparse((b'', b'') + parsed[2:])
        if not rest:
            rest = rest + b'/'
        if protocol not in self.protocols:
            print("TODO: error, unknown protocol")
            return None
        class_ = self.protocols[protocol]
        #class_ = FilterProxyFactory
        headers = self.getAllHeaders().copy()
        if b'host' not in headers:
            headers[b'host'] = host.encode('ascii')

        # Add x-forwarded-for
        headers[b'X-Forwarded-For'] = self.getClientIP().encode('ascii')

        self.content.seek(0, 0)
        s = self.content.read()
        clientFactory = class_(self.method, rest, self.clientproto, headers,
                               s, self)

        print("About to connect upstream to {}:{}".format(host, port))
        print("Headers for upstream: {}".format(headers))
        self.reactor.connectTCP(host, port, clientFactory)

class FilterProxy(proxy.Proxy):
    def __init__(self):
        super(FilterProxy, self).__init__()

    def requestFactory(self, *args):
        return FilterProxyRequest(*args)

class FilterProxyFactory(http.HTTPFactory):
    def __init__(self, *args, **kwargs):
    #self, logPath=None, timeout=60 * 60 * 12
        super(FilterProxyFactory, self).__init__()
        #http.HTTPFactory.__init__(self)

    def buildProtocol(self, addr):
        protocol = FilterProxy()
        return protocol


from twisted.internet import reactor
prox = FilterProxyFactory()
reactor.listenTCP(PROXY_PORT, prox)
reactor.run()
