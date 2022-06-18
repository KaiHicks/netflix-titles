from base64 import b64decode, b64encode
from hashlib import blake2b
from random import choice

import pytest
from app import auth
from app.database import get_db
from flask import current_app
from flask.app import Flask
from flask.testing import FlaskClient


def test_auth_page(client: FlaskClient):
    """Checks that the auth page gives status 200"""
    response = client.get("/auth/")
    assert response.status_code == 200


@pytest.mark.parametrize(
    "username, password_hash",
    [
        ("Kai", str(b64encode(b"idk man"), "utf-8")),
        ("Kai2", str(b64encode(b"something"), "utf-8")),
        ("Kai3", str(b64encode(b"somethingelse"), "utf-8")),
    ],
)
def test_register(client: FlaskClient, app: Flask, username, password_hash):
    """Checks that the registration adds the proper information to the database"""
    response = client.post(
        "/auth/register", query_string=dict(username=username, password=password_hash)
    )
    assert response.status_code == 200

    # Get the user's info from the db
    with app.app_context():
        db = get_db()
        user_row = db.execute(
            "select * from User where username=?", [username]
        ).fetchone()

    # Compute the expected hash
    hash_ = blake2b(salt=b64decode(user_row["pass_salt"]))
    hash_.update(b64decode(password_hash))
    password_hash = str(b64encode(hash_.digest()), "utf-8")

    # See if everything lines up
    assert bool(user_row), f"Could not find user, got {user_row}"
    assert user_row["username"] == username, f"Wrong username in database, got " \
        f"{user_row['username']}, expected {username}"
    assert user_row["pass_hash"] == password_hash, f"Wrong password hash in " \
        f"database, got {user_row['pass_hash']}, expected {password_hash}"


@pytest.mark.parametrize(
    "username, password_hash",
    [
        ("Kai", str(b64encode(b"idk man"), "utf-8")),
        ("Kai2", str(b64encode(b"something"), "utf-8")),
        ("Kai3", str(b64encode(b"somethingelse"), "utf-8")),
    ],
)
def test_register_login(client: FlaskClient, app: Flask, username, password_hash):
    """
    Checks that, after registering, a user can log in with the right credentials and
    that logging out removes the session from the db
    """
    # Register a new user
    response = client.post(
        "/auth/register", query_string=dict(username=username, password=password_hash)
    )
    assert response.status_code == 200

    # Log in as the new user
    response = client.post(
        "/auth/login", query_string=dict(username=username, password=password_hash)
    )
    assert 300 <= response.status_code < 400

    with app.app_context():
        # Get the user and session info from the db
        db = get_db()
        user_row = db.execute(
            "select * from User where username=?", [username]
        ).fetchone()
        sess_row = db.execute(
            "select * from Sess where user_id_=?", [user_row["user_id_"]]
        ).fetchone()
        
        # Make sure that the session exists
        assert sess_row

        # Log out the user
        response = client.post("/auth/logout")
        assert 300 <= response.status_code < 400

        # Get the session again
        sess_row = db.execute(
            "select * from Sess where user_id_=?", [user_row["user_id_"]]
        ).fetchone()

        # It should not exist because we just logged out
        assert not sess_row


@pytest.mark.parametrize(
    "username, password_hash",
    [
        ("somethinglong", str(b64encode(b"idk man"), "utf-8")),
        ("somethingelse", str(b64encode(b"something"), "utf-8")),
        ("anotherthing-", str(b64encode(b"somethingelse"), "utf-8")),
    ],
)
def test_register_login_mixed_case(
    client: FlaskClient, app: Flask, username, password_hash
):
    """Checks that logging in is case-insensitive"""
    # Register with the username in all caps
    response = client.post(
        "/auth/register",
        query_string=dict(username=username.upper(), password=password_hash),
    )
    assert response.status_code == 200

    # Log in with the username all lowercase
    response = client.post(
        "/auth/login",
        query_string=dict(username=username.lower(), password=password_hash),
    )
    assert 300 <= response.status_code < 400

    with app.app_context():
        # Get the user and session info
        db = get_db()
        user_row = db.execute(
            "select * from User where username like ?", [username]
        ).fetchone()
        sess_row = db.execute(
            "select * from Sess where user_id_=?", [user_row["user_id_"]]
        ).fetchone()

        # Make sure the session exists
        assert sess_row

        # Log out
        response = client.post("/auth/logout")
        assert 300 <= response.status_code < 400

        # Make sure there is no more session since we just logged out
        sess_row = db.execute(
            "select * from Sess where user_id_=?", [user_row["user_id_"]]
        ).fetchone()

        assert not sess_row
