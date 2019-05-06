#!/usr/bin/env python3

import sqlite3
import os
from flask import g, Flask, render_template, request

app = Flask(__name__, template_folder="template")
db_name = "database.sqlite"

def initialize_db():
	global db_name
	print("Initializing database...")
	db = sqlite3.connect(db_name, uri=True)
	db.row_factory = sqlite3.Row

	# Create flag table with real flag
	db.execute('CREATE TABLE flag (name TEXT, flag TEXT)')
	db.execute('INSERT INTO flag VALUES ("OOOps", "OOO{MuchCorporateSuchSecurity}")')

	# Create requests table
	db.execute('CREATE TABLE requests (ip TEXT, ts datetime, url TEXT, visited integer)')
	db.execute('INSERT INTO requests VALUES ("127.0.0.1", datetime("now"), "http://localhost", 0)')
	db.commit()
	print("Database setup")


def get_db():
	global db_name
	if 'db' not in g:
		if not os.path.isfile(db_name): # initialize if necessary
			initialize_db()
		

		# Now create a read-only handle for the rest of the app
		g.db = sqlite3.connect(db_name, uri=True)
		g.db.row_factory = sqlite3.Row

	return g.db

def close_db(e=None):
	db = g.pop('db', None)
	if db is not None:
		db.close()


def is_local(ip):
	return ip == "127.0.0.1" or ip == "localhost"

# Main page.
# Exploitable with SQLi:
# admin/view/0 union select 1,(select flag from flag),3,4,5
# TODO: Don't use uid?
@app.route('/admin/view/<uid>')
def view_request(uid):
	if not is_local(request.remote_addr):
		return render_template("error.html", msg="Only local users may access this website")

	con = get_db()
	cur = con.cursor()
	q = "select rowid,* from requests where rowid={}".format(uid)
	cur.execute(q)
	return render_template("view.html", row=cur.fetchone(), q=q)


# Remote users only get errors. Local users can see 404s for every other page
@app.errorhandler(404)
def page_not_found(e):
	if not is_local(request.remote_addr):
		return render_template("error.html", msg="Only local users may access this website")
	return "Page not found", 404

if __name__ == '__main__':
	app.run(debug = True, host="0.0.0.0") # TODO: use a real server and turn off debug

# vim: noet:ts=4:sw=4
