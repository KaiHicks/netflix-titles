from base64 import b64encode
import os
from re import L
import secrets
from functools import cached_property
from tempfile import mkstemp
from typing import NamedTuple

import pytest
from app import create_app, database
from bs4 import BeautifulSoup
from flask import Flask
from flask.testing import FlaskClient
from flask.wrappers import Response


class HTMLResponse(Response):
    @cached_property
    def html(self):
        return BeautifulSoup(self.get_data(), "lxml")


@pytest.fixture
def app() -> Flask:
    # Make a tempfile for the database
    db_fd, db_path = mkstemp()

    # Create a testing app using the tempfile
    app = create_app(
        {
            "flask": {
                "TESTING": True,
                "DATABASE": db_path,
                "SECRET_KEY": secrets.token_urlsafe(256 // 8),
            }
        }
    )

    with app.app_context():
        database.init_db()

    # This makes it so the responses have an `html` property that calls BeautifulSoup
    app.response_class = HTMLResponse

    # Return the app
    yield app

    # Clean up the tempfiles
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    # Get a testing client
    return app.test_client()


class AuthedClient(NamedTuple):
    client: FlaskClient
    username: str
    pass_hash: bytes
    user_id: str


@pytest.fixture
def auth_client(app: Flask) -> AuthedClient:
    """Returns an authenticated test client"""
    # Get a testing client
    client = app.test_client()
    username = "test_user"
    pass_hash = b64encode(b"badpassword")

    # Register and log in
    response = client.post(
        "/auth/register",
        query_string=dict(username=username, password=pass_hash),
    )
    assert response.status_code == 200
    response = client.post(
        "/auth/login",
        query_string=dict(username=username, password=pass_hash),
    )
    assert 300 <= response.status_code < 400

    # Get the user id from the db
    with app.app_context():
        db = database.get_db()
        cursor = db.execute(
            "select user_id_ from User where username like ?", [username]
        )
        user_id = cursor.fetchone()["user_id_"]
        cursor.close()

    return AuthedClient(client, username, pass_hash, user_id)
