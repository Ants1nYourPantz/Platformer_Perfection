from . import db
from flask_login import UserMixin
from datetime import datetime
# from flask_sqlalchemy import SQLAlchemy


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50))

    def __init__(self, username, password):
        self.username = username
        self.password = password
        db.session.add(self)
        db.session.commit()


    def __repr__(self):
        return f"<User {self.id}|{self.username}>"

    def to_dict(self):
        return {
            'username': self.username,
            'password': self.password,
        }
    
    def update_time(self, new_time):
        if self.time is None or datetime.strptime(new_time, '%H:%M:%S') < datetime.strptime(self.time, '%H:%M:%S'):
            self.time = new_time
            db.session.commit()