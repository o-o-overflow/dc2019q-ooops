#!/bin/sh
# Blocked request
http_proxy=http://OnlyOne:Overflow@127.0.0.1:8080/ curl -s http://overflow.example.com/ | grep -q "Page Blocked"
