from . import db
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, select
import datetime

class Entry(db.Model):
    __tablename__ = 'entry'
    __searchable__ = ['content']
    id = db.Column('id', db.Integer, primary_key = True)
    lang = db.Column(db.String(100))
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    city = db.Column(db.String(100))
    neighbors = db.relationship("Link", primaryjoin="Link.first_id==Entry.id")
    translations = db.relationship("Translation", backref="entry")
    retrieve = db.relationship("Retrieval", primaryjoin="Retrieval.query_id==Entry.id")
    finalized = db.relationship("FrozenLink", primaryjoin="FrozenLink.anchor_id==Entry.id")

    @hybrid_property
    def final_link_count(self):
        return self.finalized.count()
    
    @final_link_count.expression
    def final_link_count(cls):
        return (
            select([func.count(FrozenLink.other_id)]).
                where(FrozenLink.anchor_id == cls.id).
                label("final_link_count")
        )


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

    __searchable__ = ['translated']
    id = db.Column('id', db.Integer, primary_key = True)
    parent_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    model = db.Column(db.String(100))
    lang = db.Column(db.String(100))
    translated = db.Column(db.Text)

class Retrieval(db.Model):
    __tablename__ = 'retrieval'
    __table_args__ = (
        db.UniqueConstraint('query_id', 'retrieved_id', 'model', name='unique_query_retrieved_model'),
    )
    id = db.Column('id', db.Integer, primary_key = True)
    query_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    retrieved_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    score = db.Column(db.Float)
    model = db.Column(db.String(100))
    qry = db.relationship('Entry',foreign_keys=[query_id])
    ret = db.relationship('Entry',foreign_keys=[retrieved_id])


class Titles(db.Model):
    """
        Lookup table for titles in english and their translations.
    """
    __tablename__ = 'titles'
    id = db.Column('id', db.Integer, primary_key = True)
    ministry_id = db.Column(db.Integer)
    en_title = db.Column(db.Text)
    hi_title = db.Column(db.Text)
    ta_title = db.Column(db.Text)
    mr_title = db.Column(db.Text)
    gu_title = db.Column(db.Text)
    ur_title = db.Column(db.Text)
    bn_title = db.Column(db.Text)
    ml_title = db.Column(db.Text)
    te_title = db.Column(db.Text)
    or_title = db.Column(db.Text)
    pa_title = db.Column(db.Text)

class FrozenLink(db.Model):
    __tablename__ = 'frozen_link'
    __table_args__ = (
        db.UniqueConstraint('anchor_id', 'other_id', name='unique_anchor_other'),
    )

    id = db.Column('id', db.Integer, primary_key=True)
    anchor_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    other_id = db.Column(db.Integer, db.ForeignKey('entry.id'), nullable=False)
    anchor = db.relationship('Entry', foreign_keys=[anchor_id])
    other = db.relationship('Entry', foreign_keys=[other_id])

    def __repr__(self):
        return '[{id}:{lang}] -> [{oid}:{olang}]'.format(
                id=self.anchor.id, lang=self.anchor.lang,
                oid=self.other.id, olang=self.other.lang
        )

db.create_all()


