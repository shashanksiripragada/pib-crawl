from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask import render_template, request

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)


from . import models as M

@app.route('/')


@app.route('/entry/<id>')
def entry(id):
	x =  M.Entry.query.get(id)
	return render_template('entry.html', entry=x)


@app.route('/entry')
def listing():
	x =  M.Entry.query
	# x = x.filter_by(id=id)
	x = x.order_by(M.Entry.date)
	x = x.limit(5)
	x = x.all()
	print(x)
	return render_template('listing.html', entries=x)


@app.route('/parallel')
def parallel():
	src = request.args.get('src')
	tgt = request.args.get('tgt')
	src_entry =  M.Entry.query.get(src)
	tgt_entry =  M.Entry.query.get(tgt)
	return render_template('parallel.html', entries=[src_entry,tgt_entry])
