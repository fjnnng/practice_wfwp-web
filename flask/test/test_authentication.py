from source.model import database, User
from source.server import create_server
from json import loads
from pytest import fixture


@fixture(scope="module")
def server():
    yield create_server()


@fixture
def client(server):
    with server.app_context():
        database.drop_all()
        database.create_all()
        yield server.test_client()


def check_status_code(response, status_code):
    return hasattr(response, "status_code") and response.status_code == status_code


def registration(client, userpass):
    return client.post("/api/authentication/register", json=userpass)


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


def login(client, userpass):
    return client.post("/api/authentication/login", json=userpass)


def test_login_ok(client):
    userpass = {"user": "testuser", "pass": "testpass"}
    registration(client, userpass)
    response = login(client, userpass)
    assert (
        check_status_code(response, 200)
        and hasattr(response, "data")
        and "access_token" in (data := loads(response.data))
        and type(data["access_token"]) == str
    )


def test_login_unauthorized(client):
    userpass = {"user": "testuser", "pass": "testpass"}
    response = login(client, userpass)
    assert check_status_code(response, 401)
    registration(client, userpass)
    userpass["pass"] = "testwrongpass"
    response = login(client, userpass)
    assert check_status_code(response, 401)


def test_login_bad_request(client):
    response = login(client, {"user": "testuser"})
    assert check_status_code(response, 400)
    response = login(client, {"pass": "testpass"})
    assert check_status_code(response, 400)
    response = login(client, {})
    assert check_status_code(response, 400)
