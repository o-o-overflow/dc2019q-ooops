FROM ubuntu:18.04

run echo "travis_fold:start:Dapt\033[33;1mservice Dockerfile apt\033[0m" && \
    apt-get -qq update && apt-get install -qq clang python3 python3-dev python3-openssl xinetd firefox build-essential python3-virtualenv python3-setuptools wget sqlite3 gunicorn && \
    echo "\ntravis_fold:end:Dapt\r"

# Install geckodriver
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz && tar xvf geckodriver-v0.24.0-linux64.tar.gz && mv geckodriver /usr/local/bin

# Install phantomjs
RUN wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 -O phantomjs.tar.bz2 && \
  tar xvf phantomjs.tar.bz2 && \
  cp phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin/ && \
  chmod ugo+x /usr/bin/phantomjs && \
  rm -rf phantomjs-2.1.1-linux-x86_64 phantomjs.tar.bz2

# Setup users (TODO, use the users)
#   www runs public proxy
#   internal-www runs internal-only website
#   internal visits user provided urls
RUN useradd www
RUN useradd internal-www
RUN useradd internal

# Build root directory for our files
RUN mkdir /app

# Set up virtualenv and install dependencies
COPY files/requirements.txt /app/
RUN python3 -m virtualenv --python=/usr/bin/python3 /app/venv
RUN . /app/venv/bin/activate && pip install -r /app/requirements.txt

# Copy in our start script
COPY files/run.sh /app/

# Parse arguments. proxy_port default 8080, admin_www_port default 5000
ARG PROXY_PORT
ENV PROXY_PORT ${PROXY_PORT:-8080}

ARG ADMIN_WWW_PORT
ENV ADMIN_WWW_PORT ${ADMIN_WWW_PORT:-5000}

# Expose proxy port and admin_WWW (just to give a hint about local connections)
expose $PROXY_PORT $ADMIN_WWW_PORT

# Setup ssl certs into /app/cert/ca.crt, and /app/cert/ca.key
RUN mkdir /app/cert
COPY files/cert/ /app/cert/
RUN /app/cert/make_cert.sh

# Create empty requests table and non-empty flag table
COPY files/db_init.sql /app/
RUN sqlite3 /app/database.sqlite < /app/db_init.sql

# Copy in each of the 3 applications
RUN mkdir /app/internal-www
COPY files/internal-www/ /app/internal-www/

RUN mkdir /app/proxy
COPY files/proxy/ /app/proxy/

RUN mkdir /app/admin
COPY files/admin/ /app/admin/

# Start script which runs all 3 components
RUN chmod +x /app/run.sh
CMD ["/bin/sh", "-c", "/app/run.sh $ADMIN_WWW_PORT $PROXY_PORT"]
