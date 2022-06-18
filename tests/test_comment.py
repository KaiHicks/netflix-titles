from flask import Flask
from app.database import get_db
from tests.conftest import AuthedClient


def test_make_comment_db(auth_client: AuthedClient, app: Flask):
    """Makes a comment on a show and checks that it is in the database"""
    response = auth_client.client.post(
        "/film/s633/comment", data={"comment": "Love this show!"}
    )
    # 302 is a redirect status code
    assert response.status_code == 302

    # Look for the comment in the db
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            'select film_id from Comment where body = "Love this show!"'
        )
        entries = cursor.fetchall()
        cursor.close()
    assert entries


def test_make_comment_page(auth_client: AuthedClient):
    """Makes a comment on a show and checks that it is on the film page"""
    response = auth_client.client.post(
        "/film/s633/comment", data={"comment": "Love this show!"}
    )
    # 302 is a redirect status code
    assert response.status_code == 302

    # Look for the comment on the page
    response = auth_client.client.get("/film/s633")
    assert response.status_code == 200
    assert "Love this show!" in response.text


def test_make_comment_profile(auth_client: AuthedClient):
    """Makes a comment on a show and checks that it is on the user's profile"""
    response = auth_client.client.post(
        "/film/s633/comment", data={"comment": "Love this show!"}
    )
    # 302 is a redirect status code
    assert response.status_code == 302

    # Look for the comment on the page
    response = auth_client.client.get(f"/user/{auth_client.user_id}")
    assert response.status_code == 200
    assert "Love this show!" in response.text


def test_del_comment_page(auth_client: AuthedClient, app: Flask):
    """Deletes a comment on a show and checks that it is not on the film page"""
    response = auth_client.client.post(
        "/film/s633/comment", data={"comment": "Love this show!"}
    )
    # 302 is a redirect status code
    assert response.status_code == 302

    # Get the comment id so we can delete it
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            'select comment_id from Comment where body = "Love this show!"'
        )
        comment_id = cursor.fetchone()["comment_id"]
        cursor.close()

    # Delete the comment
    response = auth_client.client.post(f"/film/s633/comment/{comment_id}/delete")
    # 302 is a redirect status code
    assert response.status_code == 302

    # Look for the comment on the page, it shouldn't be there
    response = auth_client.client.get("/film/s633")
    assert response.status_code == 200
    assert "Love this show!" not in response.text


def test_edit_comment_page(auth_client: AuthedClient, app: Flask):
    """Edits a comment on a show and checks that it is edited on the film page"""
    response = auth_client.client.post(
        "/film/s633/comment", data={"comment": "Love this show!"}
    )
    # 302 is a redirect status code
    assert response.status_code == 302

    # Get the comment id so we can edit it
    with app.app_context():
        db = get_db()
        cursor = db.execute(
            'select comment_id from Comment where body = "Love this show!"'
        )
        comment_id = cursor.fetchone()["comment_id"]
        cursor.close()

    # Delete the comment
    response = auth_client.client.post(
        f"/film/s633/comment/{comment_id}/edit",
        data={"comment": "Love this show a lot!"},
    )
    # 302 is a redirect status code
    assert response.status_code == 302

    # Look for the comment on the page, the old comment shouldnt be there, but the new
    # one should be
    response = auth_client.client.get("/film/s633")
    assert response.status_code == 200
    assert "Love this show!" not in response.text
    assert "Love this show a lot!" in response.text


