from . import db
import datetime

class Entry(db.Model):
   id = db.Column('id', db.Integer, primary_key = True)
   lang = db.Column(db.String(100))
   date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
   content = db.Column(db.Text)
   city = db.Column(db.String(100))
'''
class Mapping(db.Model):
   id = db.Column('id', db.Integer, primary_key = True)
   lang = db.Column(db.String(100))
   date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
   city = db.Column(db.String(100))
'''
db.create_all()


