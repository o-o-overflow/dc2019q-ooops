#!/bin/sh

DIR=$(dirname "$0")
KEY="${DIR}/ca.key"
CRT="${DIR}/ca.crt"

openssl genrsa -out ${KEY} 2048
openssl req -new -x509 -days 365 -key ${KEY} -out ${CRT} -subj "/CN=OOO Proxy Service"
#openssl genrsa -out $(DIR)/cert.key 2048
