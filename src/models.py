from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime

class utcnow(expression.FunctionElement):
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"

db = SQLAlchemy()

class mIRCScript(db.Model):
    __tablename__ = 'mirc_scripts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(), nullable=False)
    year = db.Column(db.String(4))
    versions = db.relationship('ScriptVersion', backref='script', cascade='all,delete', foreign_keys='ScriptVersion.script_id')
    default_version = db.relationship('ScriptVersion', uselist=False, foreign_keys='mIRCScript.default_version_id')
    download_count = db.Column(db.Integer(), default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.id', ondelete='CASCADE'))
    default_version_id = db.Column(db.Integer, db.ForeignKey('script_versions.id'), unique=True)
    created_at = db.Column(db.DateTime(), default=utcnow(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=utcnow(), server_onupdate=utcnow())

class Author(db.Model):
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    name = db.Column(db.String())
    scripts = db.relationship('mIRCScript', backref='author', cascade='all,delete')
    created_at = db.Column(db.DateTime(), default=utcnow(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=utcnow(), server_onupdate=utcnow())

class ScriptVersion(db.Model):
    __tablename__ = 'script_versions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.String())
    version_number = db.Column(db.String(), nullable=False)
    download_url = db.Column(db.String())
    submitter = db.Column(db.String())
    script_id = db.Column(db.Integer(), db.ForeignKey('mirc_scripts.id', ondelete='CASCADE'))
    created_at = db.Column(db.DateTime(), default=utcnow(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=utcnow(), server_onupdate=utcnow())

class ScriptSubmission(db.Model):
    __tablename__ = "script_submissions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String())
    author = db.Column(db.String())
    version = db.Column(db.String())
    year = db.Column(db.String(4))
    description = db.Column(db.String())
    submitter = db.Column(db.String())
    upload_path = db.Column(db.String())
    upload_path = db.Column(db.String())
    approved_at = db.Column(db.DateTime())
    created_at = db.Column(db.DateTime(), default=utcnow(), nullable=False)