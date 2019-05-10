FROM ubuntu:18.04

run echo "travis_fold:start:Dapt\033[33;1mservice Dockerfile apt\033[0m" && \
    apt-get -qq update && apt-get install -qq clang python3 python3-dev python3-openssl xinetd firefox && \
    echo "\ntravis_fold:end:Dapt\r"

# Install phantomjs
#RUN wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2 -O phantomjs.tar.bz2
#RUN tar xvf phantomjs.tar.bz2
#RUN cp phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin/
#RUN chmod ugo+x /usr/bin/phantomjs

# Setup users
#   www runs public proxy
#   internal-www runs internal-only website
#   internal visits user provided urls
RUN useradd www
RUN useradd internal-www
RUN useradd internal

# Build root directory directories for admin, internal-www and proxy
RUN mkdir /app


# TODO merge with first apt install
RUN apt-get install -qq build-essential
RUN apt-get install -qq python3-virtualenv
RUN apt-get install -qq python3-setuptools

# Set up virtualenv and get dependencies
COPY files/requirements.txt /app/
RUN python3 -m virtualenv --python=/usr/bin/python3 /app/venv

RUN . /app/venv/bin/activate && pip install -r /app/requirements.txt
# Install geckodriver
RUN apt-get install -qq wget
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz && tar xvf geckodriver-v0.24.0-linux64.tar.gz && mv geckodriver /usr/local/bin

# Create table with flags  TODO merge
RUN apt-get install -qq sqlite3

# Create table with flags 
COPY files/db_init.sql /app/
RUN sqlite3 /app/database.sqlite < /app/db_init.sql

# Copy in each of the 3 components
RUN mkdir /app/admin
COPY files/admin/ /app/admin/

RUN mkdir /app/internal-www
COPY files/internal-www/ /app/internal-www/

RUN mkdir /app/proxy
COPY files/proxy/ /app/proxy/

COPY files/run.sh /app/


# Parse arguments. proxy_port default 8080, admin_ww_port default 5000
ARG PROXY_PORT
ENV PROXY_PORT ${PROXY_PORT:-8080}

ARG ADMIN_WWW_PORT
ENV ADMIN_WWW_PORT ${ADMIN_WWW_PORT:-5000}

# Ports
expose $PROXY_PORT
#TODO: Nope. Nobody gets to see this except containers
expose $ADMIN_WWW_PORT


# Start script which runs all 3 components (TODO: arg of public IP?)
RUN chmod +x /app/run.sh
CMD ["/bin/sh", "-c", "/app/run.sh $ADMIN_WWW_PORT $PROXY_PORT"]
