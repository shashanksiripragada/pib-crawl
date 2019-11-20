from . import db
import datetime

class Entry(db.Model):
    __tablename__ = 'entry'
    id = db.Column('id', db.Integer, primary_key = True)
    lang = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    content = db.Column(db.Text)
    city = db.Column(db.String(100))
    neighbors = db.relationship("Link",primaryjoin="Link.first_id==Entry.id")
    translations = db.relationship("Translation", backref="entry")
    retrieve = db.relationship("Retrieval",primaryjoin="Retrieval.query_id==Entry.id")

class Link(db.Model):
    __tablename__ = 'link'
    __table_args__ = (
        db.UniqueConstraint('first_id', 'second_id', name='unique_first_second'),
    )
    id = db.Column('id', db.Integer, primary_key = True)
    first_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    second_id = db.Column(db.Integer, db.ForeignKey('entry.id'))
    first = db.relationship('Entry',foreign_keys=[first_id])
    second = db.relationship('Entry',foreign_keys=[second_id])

class Translation(db.Model):
    __tablename__ = 'translation'
    __table_args__ = (
        db.UniqueConstraint('parent_id', 'model', name='unique_parent_model'),
    )
    id = db.Column('id', db.Integer, primary_key = True)
    parent_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    model = db.Column(db.String(100))
    lang = db.Column(db.String(100))
    translated = db.Column(db.Text)

class Retrieval(db.Model):
    __tablename__ = 'retrieval'
    __table_args__ = (
        db.UniqueConstraint('query_id', 'retrieved_id', 'model', name='unique_query_retrieved'),
    )
    id = db.Column('id', db.Integer, primary_key = True)
    query_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    retrieved_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    score = db.Column(db.Float)
    model = db.Column(db.String(100))
    q = db.relationship('Entry',foreign_keys=[query_id])
    retrieved = db.relationship('Entry',foreign_keys=[retrieved_id])

db.create_all()


