#!/bin/sh

openssl genrsa -out ca.key 2048
openssl req -new -x509 -days 365 -key ca.key -out ca.crt -subj "/CN=OOO Proxy Service"
openssl genrsa -out cert.key 2048
