from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class User(database.Model):
    username = database.Column(database.String(16), primary_key=True)
    password = database.Column(database.String(16))
