from source.model import (
    Category,
    database,
    Picture,
    PictureCategory,
    User,
    UserPicture,
)
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager,
)
from json import load
from os.path import isfile, abspath
from random import randrange

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


def add_picture(data):  # needs context and does not commit
    picture = Picture(
        sha1=data["sha1"],
        title=data["title"],
        ext=data["ext"],
        pad=data["pad"],
        size=data["size"],
        width=data["width"],
        height=data["height"],
        ratio=data["width"] / data["height"],
    )
    database.session.add(picture)
    database.session.flush()
    sha1 = data["sha1"]
    cat = int(data["cat"], 16)
    for category in categories:
        if cat & 1:
            picturecategory = PictureCategory(picture=sha1, category=category)
            database.session.add(picturecategory)
        cat >>= 1
        if not cat:
            break
    return picture


def create_server(filepath="source/data/database.json"):
    server = Flask(__name__)
    server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    database.init_app(server)
    with server.app_context():
        database.drop_all()
        database.create_all()
        for category in categories:
            database.session.add(Category(cat=category))
        database.session.commit()
        if isfile(filepath):
            with open(filepath, encoding="utf-8") as file:
                for data in load(file)["datas"]:
                    add_picture(data)
            database.session.commit()
    server.config["JWT_SECRET_KEY"] = "wfwp-web"
    jwt = JWTManager(server)

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
            and (picture := picturelike.get("picture"))
            and "like" in picturelike
            and database.session.get(Picture, picture)
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

    @server.route("/api/random", methods=["GET"])
    @jwt_required(optional=True)
    def random():
        args = request.args
        width = args.get("width", type=int, default=0)
        height = args.get("height", type=int, default=0)
        cat = args.get("cat", type=int, default=0)
        query = database.session.query(Picture)
        if width and height:
            ratio = width / height
            minratio = 3 / 4 * ratio
            maxratio = 4 / 3 * ratio
            query = query.filter(Picture.width >= width)
            query = query.filter(Picture.height >= height)
            query = query.filter(Picture.ratio >= minratio)
            query = query.filter(Picture.ratio <= maxratio)
        else:
            ratio = 0
        if cat:
            excluded_categories = []
            for category in categories:
                if cat & 1:
                    excluded_categories.append(category)
                cat >>= 1
                if not cat:
                    break
            query = query.filter(
                Picture.sha1.notin_(
                    database.session.query(PictureCategory.picture).filter(
                        PictureCategory.category.in_(excluded_categories)
                    )
                )
            )
        if user := get_jwt_identity():
            query = query.filter(
                Picture.sha1.notin_(
                    database.session.query(UserPicture.picture).filter(
                        UserPicture.user == user
                    )
                )
            )
        if count := query.count():
            picture = query.offset(randrange(count)).limit(1).first()
        else:
            return "", 404
        if ratio:
            if picture.ratio > ratio:
                scaling = round(height * picture.ratio)
            else:
                scaling = width
        else:
            scaling = 0
        query = database.session.query(UserPicture).filter(
            UserPicture.picture == picture.sha1
        )
        return (
            jsonify(
                {
                    "file": picture.title + "." + picture.ext,
                    "pad": picture.pad,
                    "scaling": scaling,
                    "sha1": picture.sha1,
                    "size": picture.size,
                    "like": query.filter(UserPicture.like == True).count(),
                    "dislike": query.filter(UserPicture.like == False).count(),
                    "count": count,
                }
            ),
            200,
        )

    return server


if __name__ == "__main__":
    server = create_server()
    server.run(debug=True)
