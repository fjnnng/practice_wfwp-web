from source.model import Category, database, Picture, PictureCategory, User, UserPicture
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager,
)

categories = [
    "Arthropods",
    "Birds",
    "People",
    "Amphibians",
    "Fish",
    "Reptiles",
    "Other Animals",
    "Bones/Fossils",
    "Shells",
    "Plants",
    "Fungi",
    "Other lifeforms",
    "Rocks/Minerals",
    "Cemeteries",
    "Religious Buildings/Art",
    "Computer-generated Pictures",
]


def initialize_database():
    for category in categories:
        database.session.add(Category(cat=category))
    database.session.commit()


def add_picture(data):  # does not commit
    picture = Picture(
        sha1=data["sha1"],
        title=data["title"],
        ext=data["ext"],
        pad=data["pad"],
        size=data["size"],
        width=data["width"],
        height=data["height"],
    )
    database.session.add(picture)
    database.session.flush()
    sha1 = data["sha1"]
    cat = data["cat"]
    for category in categories:
        if cat & 1:
            picturecategory = PictureCategory(picture=sha1, category=category)
            database.session.add(picturecategory)
        cat >>= 1


def create_server():
    server = Flask(__name__)
    server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    database.init_app(server)
    server.config["JWT_SECRET_KEY"] = "wfwp-web"
    jwt = JWTManager(server)
    with server.app_context():
        database.create_all()
        initialize_database()

    @server.route("/api/authentication/register", methods=["POST"])
    def register():
        userpass = request.get_json()
        if type(userpass) == dict and "user" in userpass and "pass" in userpass:
            if database.session.get(User, userpass["user"]):
                return "", 409
            database.session.add(
                User(username=userpass["user"], password=userpass["pass"])
            )
            database.session.commit()
            return "", 201
        return "", 400

    @server.route("/api/authentication/login", methods=["POST"])
    def login():
        userpass = request.get_json()
        if type(userpass) == dict and "user" in userpass and "pass" in userpass:
            if (
                user := database.session.get(User, userpass["user"])
            ) and user.password == userpass["pass"]:
                return (
                    jsonify(access_token=create_access_token(identity=user.username)),
                    200,
                )
            return "", 401
        return "", 400

    @server.route("/api/like", methods=["POST"])
    @jwt_required()  # other codes are returned automatically
    def like():
        user = get_jwt_identity()
        picturelike = request.get_json()
        if (
            type(picturelike) == dict
            and "picture" in picturelike
            and "like" in picturelike
            and database.session.get(Picture, picture := picturelike["picture"])
        ):
            if userpicture := database.session.get(
                UserPicture, {"user": user, "picture": picture}
            ):
                database.session.delete(userpicture)
            if (like := picturelike["like"]) != None:
                userpicture = UserPicture(user=user, picture=picture, like=like)
                database.session.add(userpicture)
            database.session.commit()
            return "", 200
        return "", 400

    return server


if __name__ == "__main__":
    server = create_server()
    server.run(debug=True)
