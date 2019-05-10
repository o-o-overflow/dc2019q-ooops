#!/usr/bin/env python3

import sqlite3
import os
from flask import g, Flask, render_template, request, send_file

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


def is_local(request):
	"""
	Check if this request is from an internal IP. If x-forwarded-for header, use that
	"""
	def is_local_ip(ip):
		return ip == "127.0.0.1" or ip == "localhost" or ip == PUBLIC_IP

	# Check every possible X-forwarded-header to see if any are non-local
	# IPs. If so, return false
	for k,v in request.headers:
		if k.lower() == "x-forwarded-for":
			if not(is_local_ip(v)):
				return False

	# Without x-forwarded, just check IP directly. Should only happen for our admin grader
	ip = request.remote_addr
	return ip == "127.0.0.1" or ip == "localhost" or ip == PUBLIC_IP

# Home. Just so it's clear this is a website
@app.route('/')
def home():
	if not is_local(request):
		return render_template("error.html", msg="Only internal users may access this website")
	return render_template("home.html")

# Main page.
# Exploitable with SQLi:
# admin/view/0 union select 1,(select flag from flag),3,4,5
# TODO: Don't use uid?
@app.route('/admin/view/<uid>')
def view_request(uid):
	if not is_local(request):
		return render_template("error.html", msg="Only internal users may access this website")

	con = get_db()
	cur = con.cursor()
	q = "select rowid,* from requests where rowid={};".format(uid) # XXX: Exploitable :)
	cur.execute(q)
	row = cur.fetchone()
	try:
		url = row["url"].decode("ascii")
	except Exception as e:
		print("Exception decoding URL from db {}. Possible SQLi attempt: {}".format(e, url))
		url = "error"
	return render_template("view.html", row=row, url=url, q=q)

@app.route('/css/bootstrap.min.css')
def css():
	return send_file("css/bootstrap.min.css")

# Remote users only get errors. Local users can see 404s for every other page
@app.errorhandler(404)
def page_not_found(e):
	if not is_local(request):
		return render_template("error.html", msg="Only local users may access this website")
	return "Page not found", 404

def gunicorn_start(*args, **kwargs):
	# Entry point for gunicorn, pulls public ip from environment
	global PUBLIC_IP
	PUBLIC_IP = os.environ['CONTAINER_IP']
	print("INTERNAL-WWW started with {}".format(PUBLIC_IP))
	return app


if __name__ == '__main__':
	import sys
	assert(len(sys.argv) == 3), "Usage: ./internal.py [Public IP] [Port]"

	global PUBLIC_IP
	PUBLIC_IP = sys.argv[1]

	# TODO use a real webserver? Won't have much traffic
	#app.run(debug = True, host=PUBLIC_IP, port=int(sys.argv[2]))
	app.run(debug = False, host=PUBLIC_IP, port=int(sys.argv[2]))



# vim: noet:ts=4:sw=4
