#!/bin/sh
set -e

if [ "$#" -ne 2 ]; then
  echo "USAGE: $0 [Admin_port] [Proxy_port]"
  exit 1
fi

ADMIN_PORT=$1 # for internal-www interface, not the actual admin.py script
PROXY_PORT=$2
CONTAINER_IP=$(awk 'END{print $1}' /etc/hosts)

echo "Started with AP=$ADMIN_PORT, PP=$PROXY_PORT, CIP=$CONTAINER_IP"

echo "Activate venv"
. /app/venv/bin/activate

echo "Start internal" # TODO: run as internalwww?
cd /app/internalwww
CONTAINER_IP=$CONTAINER_IP /app/venv/bin/gunicorn --workers=2 -b $CONTAINER_IP:$ADMIN_PORT internalwww:app &
cd /

echo "Start proxy"
#sudo -su www /app/venv/bin/python /app/proxy/run-proxy.py $CONTAINER_IP $PROXY_PORT &
/app/venv/bin/python /app/proxy/run-proxy.py $CONTAINER_IP $PROXY_PORT &

echo "Start 3 admin processes"
#sudo -su internal /app/venv/bin/python /app/admin/admin.py $CONTAINER_IP $ADMIN_PORT $PROXY_PORT &
/app/admin/admin.py $CONTAINER_IP $ADMIN_PORT $PROXY_PORT &
/app/admin/admin.py $CONTAINER_IP $ADMIN_PORT $PROXY_PORT &
/app/admin/admin.py $CONTAINER_IP $ADMIN_PORT $PROXY_PORT
