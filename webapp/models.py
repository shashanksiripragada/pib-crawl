from . import db
import datetime

class Entry(db.Model):
    __tablename__ = 'entry'
    id = db.Column('id', db.Integer, primary_key = True)
    lang = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    content = db.Column(db.Text)
    city = db.Column(db.String(100))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)



class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column('id', db.Integer, primary_key = True)
    entries = db.relationship('Entry', backref='group', lazy=True)

db.create_all()


