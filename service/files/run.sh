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

echo "Start internal"
/app/internal-www/internal.py $CONTAINER_IP $ADMIN_PORT &
#cd /app/internal-www
#gunicorn -b $CONTAINER_IP:$ADMIN_PORT --pythonpath=$(which python) internal-www:gunicorn_start

echo "Start proxy"
/app/proxy/run-proxy.py $CONTAINER_IP $PROXY_PORT &

echo "Start admin"
/app/admin/admin.py $CONTAINER_IP $ADMIN_PORT $PROXY_PORT
