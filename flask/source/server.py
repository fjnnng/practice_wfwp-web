from source.model import database, User
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    JWTManager,
)


def create_server():
    server = Flask(__name__)
    server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    database.init_app(server)
    server.config["JWT_SECRET_KEY"] = "wfwp-web"
    jwt = JWTManager(server)

    @server.route("/api/authentication/register", methods=["POST"])
    def register():
        userpass = request.get_json()
        if "user" in userpass and "pass" in userpass:
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
        if "user" in userpass and "pass" in userpass:
            if (
                user := database.session.get(User, userpass["user"])
            ) and user.password == userpass["pass"]:
                return (
                    jsonify(access_token=create_access_token(identity=user.username)),
                    200,
                )
            return "", 401
        return "", 400

    @server.route("/api/protected", methods=["GET"])
    @jwt_required()  # return codes other than 200 automatically
    def protected():
        return jsonify(logged_in_as=get_jwt_identity()), 200

    return server


if __name__ == "__main__":
    server = create_server()
    server.run(debug=True)
