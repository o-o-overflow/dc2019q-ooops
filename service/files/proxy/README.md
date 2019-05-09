Proxy
===
Simple Twisted proxy which rewrites requests to `/prox-internal/....` to local files.

Rewrites requests to urls containing the string `overflow` to serve [prox-internal/blocked.html](blocked.html)

Introduces a cross-site scripting vulnerability in [prox-internal/scripts/main.js](main.js).

Since the `/prox-internal/...` paths are intercepted on all domains, the XSS vulnerability becomes a universal XSS bug.
