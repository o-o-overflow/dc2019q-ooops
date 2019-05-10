#!/usr/bin/env python3

import sqlite3
import os
from flask import g, Flask, render_template, request, send_file
from base64 import b64decode

# Configuration
DB_NAME = "file:///app/database.sqlite?mode=ro"
# End configuration

app = Flask(__name__, template_folder="template")

def get_db():
	global DB_NAME
	if 'db' not in g:
		# Now create a read-only handle for the rest of the app
		g.db = sqlite3.connect(DB_NAME, uri=True)
		g.db.row_factory = sqlite3.Row

	return g.db

def close_db(e=None):
	db = g.pop('db', None)
	if db is not None:
		db.close()


def is_local(ip):
	return ip == "127.0.0.1" or ip == "localhost" or ip == PUBLIC_IP

# Home. Just so it's clear this is a website
@app.route('/')
def home():
	if not is_local(request.remote_addr):
		return render_template("error.html", msg="Only internal users may access this website")
	return render_template("home.html")

# Main page.
# Exploitable with SQLi:
# admin/view/0 union select 1,(select flag from flag),3,4,5
# TODO: Don't use uid?
@app.route('/admin/view/<uid>')
def view_request(uid):
	if not is_local(request.remote_addr):
		return render_template("error.html", msg="Only internal users may access this website")

	con = get_db()
	cur = con.cursor()
	q = "select rowid,* from requests where rowid={};".format(uid) # XXX: Exploitable :)
	cur.execute(q)
	row = cur.fetchone()
	try:
		url = b64decode(row["url"]).decode("utf-8")
		print(url)
	except Exception as e:
		print(e)
		url = "error"
	return render_template("view.html", row=row, url=url, q=q)

@app.route('/css/bootstrap.min.css')
def css():
	#if not is_local(request.remote_addr):
	#	return render_template("error.html", msg="Only local users may access this website")
	return send_file("css/bootstrap.min.css")

# Remote users only get errors. Local users can see 404s for every other page
@app.errorhandler(404)
def page_not_found(e):
	if not is_local(request.remote_addr):
		return render_template("error.html", msg="Only local users may access this website")
	return "Page not found", 404

if __name__ == '__main__':
	import sys
	assert(len(sys.argv) == 3), "Usage: ./internal.py [Public IP] [Port]"

	global PUBLIC_IP
	PUBLIC_IP = sys.argv[1]

	# TODO use a real webserver w/o debug
	app.run(debug = True, host=PUBLIC_IP, port=int(sys.argv[2]))

# vim: noet:ts=4:sw=4
