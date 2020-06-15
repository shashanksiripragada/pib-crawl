from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pib-crawled-sqlite.db'

db = SQLAlchemy(app)

# Search didn't work as nicely.
# from flask_msearch import Search
# import logging
# # when backend is elasticsearch, MSEARCH_INDEX_NAME is unused
# # simple,whoosh,elaticsearch, default is simple
# MSEARCH_BACKEND = 'whoosh'
# # table's primary key if you don't like to use id, or set __msearch_primary_key__ for special model
# MSEARCH_PRIMARY_KEY = 'id'
# # auto create or update index
# MSEARCH_ENABLE = True
# # logger level, default is logging.WARNING
# MSEARCH_LOGGER = logging.DEBUG
# # SQLALCHEMY_TRACK_MODIFICATIONS must be set to True when msearch auto index is enabled
# SQLALCHEMY_TRACK_MODIFICATIONS = True
# # when backend is elasticsearch
# search = Search(db=db)
# search.init_app(app)
# search.create_index()

from . import models as M
is_sqlite = True
migrate = Migrate(app, db, render_as_batch=is_sqlite)

from .docstore import docstore
app.register_blueprint(docstore)

