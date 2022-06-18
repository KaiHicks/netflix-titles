import json
import secrets
from os import environ
from tempfile import mkstemp
from urllib.parse import quote_plus

from flask import Flask

from app import database

from . import auth, film, home, person, user

TEMPLATES_AUTO_RELOAD = True

def create_app(config=None) -> Flask:
	app = Flask(__name__)
	
	# Add stuff to jinja engine
	app.jinja_env.filters['quote_plus'] = quote_plus
	app.jinja_env.line_statement_prefix = '#'
	app.add_template_global(auth.get_sess_info, 'get_sess_info')
	
	# Set the secret key
	if 'FLASK_SECRET_KEY' not in environ:
		print('No secret key found, generating a new one')
		environ['FLASK_SECRET_KEY'] = secrets.token_urlsafe(256//8)
	app.config['SECRET_KEY'] = environ['FLASK_SECRET_KEY']
	
	if config is None:
		# Load config
		with open('config.json', 'r') as cf:
			config = json.load(cf)
	if 'DATABASE' not in config.get('flask', {}):
		_, db_path = mkstemp()
		config['flask']['DATABASE'] = db_path
	for k, v in config.get('flask', {}).items():
		print(k, v)
		app.config[k] = v
	
	with app.app_context():
		if config.get('init_db', False):
			database.init_db(config.get('testing', False))
	
	# Register blueprints
	app.register_blueprint(home.bp)
	app.register_blueprint(film.bp)
	app.register_blueprint(person.bp)
	app.register_blueprint(auth.bp)
	app.register_blueprint(user.bp)
	
	# Setup database
	# with app.app_context():
	# 	database.init_db()
	
	return app
