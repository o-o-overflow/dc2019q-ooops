#!/bin/sh

# Note this only works if we're actually exposing the internal server
#curl http://127.0.0.1:5000 | grep -q "only internal users may access"

http_proxy=http://OnlyOne:Overflow@127.0.0.1:8080/ curl -s 172.17.0.2:5000
