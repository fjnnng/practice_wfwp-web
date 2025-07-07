from source.model import database, User, UserPicture
from source.server import add_picture, create_server
from json import loads
from pytest import fixture


@fixture(scope="module")
def server():
    yield create_server()


@fixture
def client(server):
    with server.app_context():
        database.session.query(UserPicture).delete()
        database.session.query(User).delete()
        yield server.test_client()


def check_status_code(response, status_code):
    return hasattr(response, "status_code") and response.status_code == status_code


def registration(client, userpass):
    return client.post("/api/authentication/register", json=userpass)


def test_registration(client):
    response = registration(client, {})
    assert check_status_code(response, 400)
    response = registration(client, {"user": "testuser"})
    assert check_status_code(response, 400)
    response = registration(client, {"pass": "testpass"})
    assert check_status_code(response, 400)
    userpass = {"user": "testuser", "pass": "testpass"}
    response = registration(client, userpass)
    assert (
        check_status_code(response, 201)
        and (user := database.session.get(User, userpass["user"]))
        and user.password == "testpass"
    )
    response = registration(client, userpass)
    assert check_status_code(response, 409)


def login(client, userpass):
    return client.post("/api/authentication/login", json=userpass)


def test_login(client):
    response = login(client, {})
    assert check_status_code(response, 400)
    response = login(client, {"user": "testuser"})
    assert check_status_code(response, 400)
    response = login(client, {"pass": "testpass"})
    assert check_status_code(response, 400)
    userpass = {"user": "testuser", "pass": "testpass"}
    response = login(client, userpass)
    assert check_status_code(response, 401)
    registration(client, userpass)
    userwrongpass = {"user": "testuser", "pass": "testwrongpass"}
    response = login(client, userwrongpass)
    assert check_status_code(response, 401)
    response = login(client, userpass)
    assert (
        check_status_code(response, 200)
        and hasattr(response, "data")
        and type(loads(response.data).get("access_token")) == str
    )


def like(client, token, picture, like):
    return client.post(
        "/api/like",
        headers={"Authorization": f"Bearer " + token},
        json={"picture": picture, "like": like},
    )


def test_like(client):
    response = client.post("/api/like")
    assert not check_status_code(response, 200)
    response = client.post("/api/like", headers={"Authorization": "Bearer testtoken"})
    assert not check_status_code(response, 200)
    userpass = {"user": "testuser", "pass": "testpass"}
    registration(client, userpass)
    token = loads(login(client, userpass).data)["access_token"]
    response = client.post("/api/like", headers={"Authorization": f"Bearer " + token})
    assert not check_status_code(response, 200)
    response = client.post(
        "/api/like",
        headers={"Authorization": f"Bearer " + token},
        json={},
    )
    assert check_status_code(response, 400)
    response = client.post(
        "/api/like",
        headers={"Authorization": f"Bearer " + token},
        json={"picture": ""},
    )
    assert check_status_code(response, 400)
    response = client.post(
        "/api/like",
        headers={"Authorization": f"Bearer " + token},
        json={"like": None},
    )
    assert check_status_code(response, 400)
    sha1 = "0123456789abcdef"
    response = like(client, token, sha1, None)
    assert check_status_code(response, 400)
    data = {
        "sha1": sha1,
        "title": "testtitle",
        "ext": "jpeg",
        "pad": "0/12",
        "size": 1048576,
        "width": 1920,
        "height": 1080,
        "cat": "1",
    }
    with client.application.app_context():
        picture = add_picture(data)
        database.session.commit()
    response = like(client, token, sha1, True)
    user = userpass["user"]
    assert (
        check_status_code(response, 200)
        and (
            userpicture := database.session.get(
                UserPicture, {"user": user, "picture": sha1}
            )
        )
        and userpicture.like == True
    )
    response = like(client, token, sha1, False)
    assert (
        check_status_code(response, 200)
        and (
            userpicture := database.session.get(
                UserPicture, {"user": user, "picture": sha1}
            )
        )
        and userpicture.like == False
    )
    response = like(client, token, sha1, None)
    assert check_status_code(response, 200) and not database.session.get(
        UserPicture, {"user": user, "picture": sha1}
    )
    with client.application.app_context():
        database.session.delete(picture)
        database.session.commit()


def random(client, args, token=None):
    if token:
        return client.get(
            "/api/random",
            query_string=args,
            headers={"Authorization": f"Bearer " + token},
        )
    return client.get("/api/random", query_string=args)


def test_random(client):
    response = random(client, {})
    assert check_status_code(response, 200) and hasattr(response, "json")
    print(type(response.json))
    count = response.json.get("count", 0)
    assert type(count) == int and count > 0
    response = random(client, {"width": 1920, "height": 1080})
    assert check_status_code(response, 200) and hasattr(response, "json")
    newcount = response.json.get("count", 0)
    assert type(newcount) == int and 0 < newcount < count
    count = newcount
    response = random(client, {"width": 1920, "height": 1080, "cat": 1})
    assert check_status_code(response, 200) and hasattr(response, "json")
    newcount = response.json.get("count", 0)
    assert type(newcount) == int and 0 < newcount < count
    count = newcount
    sha1 = response.json.get("sha1", "")
    assert type(sha1) == str
    userpass = {"user": "testuser", "pass": "testpass"}
    registration(client, userpass)
    token = loads(login(client, userpass).data)["access_token"]
    like(client, token, sha1, True)
    response = random(client, {"width": 1920, "height": 1080, "cat": 1}, token)
    assert check_status_code(response, 200) and hasattr(response, "json")
    newcount = response.json.get("count", 0)
    assert type(newcount) == int and newcount == count - 1
    count = newcount
    like(client, token, sha1, False)
    response = random(client, {"width": 1920, "height": 1080, "cat": 1}, token)
    assert check_status_code(response, 200) and hasattr(response, "json")
    newcount = response.json.get("count", 0)
    assert type(newcount) == int and newcount == count
    like(client, token, sha1, None)
    response = random(client, {"width": 1920, "height": 1080, "cat": 1}, token)
    assert check_status_code(response, 200) and hasattr(response, "json")
    newcount = response.json.get("count", 0)
    assert type(newcount) == int and newcount == count + 1
