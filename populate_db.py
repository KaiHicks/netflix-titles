"""
Generates the sql to populate the database with the data from the given .csv.
The sql commands are this.outputed to stdout. 

Usage: python3 populate_db.py <path to csv file>
"""

import datetime as dt
import secrets
from collections import namedtuple
from datetime import datetime
from random import choice, random, randrange
from sys import argv, modules, stderr
from typing import Counter

import pandas as pd

this = modules[__name__]
this.output = print
this.testing = False

def insert_film(row):
	# Format the date
	date_added = row.date_added
	# Some are blank and are imported as nan
	if isinstance(date_added, float):
		date_added = f'January 1, {row.release_year}'
	# Some have leading spaces
	date_added = date_added.strip()
	date_added = datetime.strptime(date_added, '%B %d, %Y')
	date_added = date_added.strftime('%Y-%m-%d')
	
	# fixing the rating
	rating = row.rating
	if isinstance(rating, float):
		rating = 'UR*'
	
	# Escape any single quotes. This is not a typo, sql uses double single
	# quotes
	show_id = row.show_id.replace("\'", "\'\'")
	title = row.title.replace("\'", "\'\'")
	type_ = row.type.replace("\'", "\'\'")
	rating = rating.replace("\'", "\'\'")
	duration = row.duration.replace("\'", "\'\'")
	release_year = int(row.release_year)
	description = row.description.replace("\'", "\'\'")
	this.output(f'insert into Film values(\'{show_id}\', \'{title}\', ' \
		f'\'{type_}\', {release_year}, \'{date_added}\', \'{rating}\', ' \
		f'\'{duration}\', \'{description}\', {random()});')
	
	# In testing mode, we make fake comments
	if this.testing:
		start_date = dt.date(2020, 1, 1)
		end_date = dt.date(2021, 1, 1)
		delta = (end_date - start_date).days
		for i in range(randrange(2, 10)):
			user = choice(this.fake_users)
			date = start_date + dt.timedelta(days=randrange(delta))
			this.output(f'''
				insert into Comment values(
					"commentid_{secrets.token_urlsafe(256//8)}",
					"{user.user_id}",
					"{show_id}",
					"{date}",
					"This is a fake comment for testing purposes"
				)
			''')

relationships = Counter()
def insert_relationship(film_id, other_key, table):
	if not other_key.strip():
		return
	
	other_key = other_key.replace("\'", "\'\'")
	this.output(f'insert into {table} values(\'{film_id}\', \'{other_key}\');')
	relationships[f'insert into {table} values(\'{film_id}\', \'{other_key}\');'] += 1

def insert_relationships(row, deliminator=', '):
	# actors
	cast = row.cast if isinstance(row.cast, str) else ''
	for person in set(cast.split(deliminator)):
		insert_relationship(row.show_id, person, 'Acted')
	
	# directors
	director = row.director if isinstance(row.director, str) else ''
	for person in set(director.split(deliminator)):
		insert_relationship(row.show_id, person, 'Directed')
	
	# locations
	country = row.country if isinstance(row.country, str) else ''
	for country in set(country.split(deliminator)):
		insert_relationship(row.show_id, country, 'Produced')
	
	listed_in = row.listed_in if isinstance(row.listed_in, str) else ''
	# genres
	for genre in set(listed_in.split(deliminator)):
		insert_relationship(row.show_id, genre, 'Listed')

User = namedtuple('User', 'user_id, username')
fake_users = []
n_fake_users = 10

def run(csv_path, out=None, testing=False):
	this.output = out or print
	this.testing = testing
	
	this.output('begin transaction;')
	
	# in testing mode, we create some users
	if testing:
		for i in range(n_fake_users):
			fake_user = User(f'userid_FAKE-{i}', f'FakeUser-{i}')
			fake_users.append(fake_user)
			this.output(f'''insert into User values(
				"{fake_user.user_id}",
				"{fake_user.username}",
				"abcd",
				"abcd"
			)''')
	
	csv = pd.read_csv(csv_path)

	for row in csv.itertuples():
		insert_film(row)
		insert_relationships(row)
	
	this.output('end transaction;')

if __name__ == '__main__':
	if len(argv) == 1:
		this.output('Not enough arguments!', file=stderr)
		this.output('Usage: python3 populate_db.py <path to csv file>', file=stderr)
		exit(1)
	
	run(argv[1])
