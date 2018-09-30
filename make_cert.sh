#!/bin/sh

mkdir cert
openssl genrsa -out cert/ca.key 2048
openssl req -new -x509 -days 365 -key cert/ca.key -out cert/ca.crt -subj "/CN=Corp Proxy"
openssl genrsa -out cert/cert.key 2048
