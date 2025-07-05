from source.model import database, User
from flask import Flask, request


def create_server():
    server = Flask(__name__)
    server.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    database.init_app(server)

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

    return server


if __name__ == "__main__":
    server = create_server()
    server.run(debug=True)
