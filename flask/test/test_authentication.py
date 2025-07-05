from source.model import database, User
from source.server import create_server
from pytest import fixture


@fixture(scope="module")
def server():
    server = create_server()
    with server.app_context():
        database.create_all()
        yield server
        database.drop_all()


@fixture
def client(server):
    return server.test_client()


def registration(client, userpass):
    return client.post("/api/authentication/register", json=userpass)


def check_status_code(response, status_code):
    return hasattr(response, "status_code") and response.status_code == status_code


def test_registration_created(client):
    userpass = {"user": "testuser", "pass": "testpass"}
    response = registration(client, userpass)
    assert (
        check_status_code(response, 201)
        and (user := database.session.get(User, userpass["user"]))
        and user.password == "testpass"
    )


def test_registration_conflict(client):
    userpass = {"user": "testuser", "pass": "testpass"}
    response = registration(client, userpass)
    response = registration(client, userpass)
    assert check_status_code(response, 409)


def test_registration_bad_request(client):
    response = registration(client, {"user": "testuser"})
    assert check_status_code(response, 400)
    response = registration(client, {"pass": "testpass"})
    assert check_status_code(response, 400)
    response = registration(client, {})
    assert check_status_code(response, 400)
