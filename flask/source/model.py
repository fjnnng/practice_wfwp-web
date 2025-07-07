from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class User(database.Model):
    username = database.Column(database.String(16), primary_key=True)
    password = database.Column(database.String(16))


class Picture(database.Model):
    sha1 = database.Column(database.String(40), primary_key=True)
    title = database.Column(database.String(512))
    ext = database.Column(database.String(4))
    pad = database.Column(database.String(4))
    size = database.Column(database.Integer)
    width = database.Column(database.Integer)
    height = database.Column(database.Integer)
    ratio = database.Column(database.Float)


class Category(database.Model):
    cat = database.Column(database.String(27), primary_key=True)


class PictureCategory(database.Model):
    picture = database.Column(
        database.String(40), database.ForeignKey("picture.sha1"), primary_key=True
    )
    category = database.Column(
        database.String(27), database.ForeignKey("category.cat"), primary_key=True
    )


class UserPicture(database.Model):
    user = database.Column(
        database.String(16), database.ForeignKey("user.username"), primary_key=True
    )
    picture = database.Column(
        database.String(40), database.ForeignKey("picture.sha1"), primary_key=True
    )
    like = database.Column(database.Boolean, nullable=False)
    __table_args__ = (database.UniqueConstraint("user", "picture"),)
