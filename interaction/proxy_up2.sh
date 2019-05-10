#!/bin/sh

# Unblocked request
http_proxy=http://OnlyOne:Overflow@127.0.0.1:8080/ curl -s http://example.com/ | grep -q "This domain is established"
