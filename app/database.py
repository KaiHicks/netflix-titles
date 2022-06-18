import os
import sqlite3
from os import environ
from tempfile import mkstemp

import click
import populate_db
from flask import current_app, g
from flask.cli import with_appcontext


def connect_db() -> sqlite3.Connection:
	"""
	Initializes the connection to a temporary database

	Returns:
		sqlite3.Connection: The database connection
	"""
	# Make the tempfile
	db_fd, db_path = mkstemp()
	# Connect to the database. This will use the tempfile if specified in the config
	db = sqlite3.connect(
		environ.get('DATABASE', current_app.config['DATABASE'])
	)
	db.row_factory = sqlite3.Row
	g.db_fd = db_fd
	g.db_path = db_path
	return db

def get_db() -> sqlite3.Connection:
	if not hasattr(g, 'db'):
		g.db = connect_db()
	return g.db

def close_db():
	print('Closing db')
	if hasattr(g, 'db'):
		g.db.close()
	# Clean up the temp files
	if hasattr(g, 'db_fd'):
		os.close(g.db_fd)
	if hasattr(g, 'db_path'):
		os.unlink(g.db_path)

def init_db(testing=False):
	print('Initializing db')
	db = get_db()
	# Initialize the database 
	with current_app.open_resource('../query-create-database.sql') as f:
		db.executescript(f.read().decode('utf-8'))
	db.commit() 
	# Populate it using the dataset
	populate_db.run('netflix_titles.csv', out=db.execute, testing=testing)
	db.commit() 
	print('done')

@click.command('init-db')
@with_appcontext
def init_db_command():
	init_db()
	click.echo('Initilized the db.')
