"""
models.py — SQLAlchemy ORM models for The Climate Mirror.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), unique=True, nullable=False)
    password   = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    history    = db.relationship("HistoryRecord", backref="user", lazy=True)
    notes      = db.relationship("Note", backref="user", lazy=True)
    chat_logs  = db.relationship("ChatLog", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class HistoryRecord(db.Model):
    __tablename__ = "history"
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(80), db.ForeignKey("users.username"), nullable=False)
    country      = db.Column(db.String(64))
    emission     = db.Column(db.Float, default=0.0)
    energy       = db.Column(db.Float, default=0.0)
    transport    = db.Column(db.Float, default=0.0)
    industry     = db.Column(db.Float, default=0.0)
    temp         = db.Column(db.Float)
    impact       = db.Column(db.String(64))
    summary      = db.Column(db.Text)
    agent_advice = db.Column(db.Text)   # JSON
    disaster_risk= db.Column(db.Text)   # JSON
    story        = db.Column(db.Text)   # JSON
    policy       = db.Column(db.Text)   # JSON
    comparator   = db.Column(db.Text)   # JSON
    analysis     = db.Column(db.Text)   # JSON
    score        = db.Column(db.Integer, default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Note(db.Model):
    __tablename__ = "notes"
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), db.ForeignKey("users.username"), nullable=False)
    title      = db.Column(db.String(200))
    content    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatLog(db.Model):
    __tablename__ = "chat_logs"
    id         = db.Column(db.Integer, primary_key=True)
    username   = db.Column(db.String(80), db.ForeignKey("users.username"), nullable=False)
    message    = db.Column(db.Text)
    response   = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AgentRun(db.Model):
    __tablename__ = "agent_runs"
    id               = db.Column(db.Integer, primary_key=True)
    username         = db.Column(db.String(80), db.ForeignKey("users.username"), nullable=False)
    history_id       = db.Column(db.Integer, db.ForeignKey("history.id"))
    orchestrator_log = db.Column(db.Text)   # JSON
    total_agents_run = db.Column(db.Integer)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
