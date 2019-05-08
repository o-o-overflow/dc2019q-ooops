#!/usr/bin/env python3

PUBLIC_IP = "192.168.1.159"

import sqlite3
import os
from flask import g, Flask, render_template, request, send_file

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

	db.execute('INSERT INTO requests VALUES ("127.0.0.1", datetime("now"), "http://state.actor/log.php?v=1", 0)')
	db.execute('INSERT INTO requests VALUES ("127.0.0.1", datetime("now"), "http://state.actor/log.php?v=2", 0)')
	db.execute('INSERT INTO requests VALUES ("127.0.0.1", datetime("now"), "http://state.actor/log.php?v=3", 0)')

	db.execute('INSERT INTO requests VALUES ("2.2.2.2", datetime("now"), "http://state.actor/log.php?v=2_1", 0)')
	db.execute('INSERT INTO requests VALUES ("2.2.2.2", datetime("now"), "http://state.actor/log.php?v=2_2", 0)')
	db.execute('INSERT INTO requests VALUES ("2.2.2.2", datetime("now"), "http://state.actor/log.php?v=2_3", 0)')



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
	return ip == "127.0.0.1" or ip == "localhost" or ip == PUBLIC_IP

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
	q = "select rowid,* from requests where rowid={};".format(uid)
	cur.execute(q)
	row = cur.fetchone()
	return render_template("view.html", row=row, q=q)

@app.route('/css/bootstrap.min.css')
def css():
	if not is_local(request.remote_addr):
		return render_template("error.html", msg="Only local users may access this website")
	return send_file("css/bootstrap.min.css")

# Remote users only get errors. Local users can see 404s for every other page
@app.errorhandler(404)
def page_not_found(e):
	if not is_local(request.remote_addr):
		return render_template("error.html", msg="Only local users may access this website")
	return "Page not found", 404

if __name__ == '__main__':
	app.run(debug = True, host=PUBLIC_IP) # TODO: use a real server and turn off debug
	#app.run(debug = True) #TODO

# vim: noet:ts=4:sw=4
