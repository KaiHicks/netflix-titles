from flask.testing import FlaskClient


def test_tv_page(client: FlaskClient):
    """Checks the info on a tv show's page"""
    # Using this show as a test vector
    response = client.get("/film/s633")
    assert response.status_code == 200

    # Make sure the title, type, and a couple of names are correct
    content = response.data.decode("utf-8")
    assert "Avatar: The Last Airbender" in content
    assert "TV Show" in content
    assert "Dante Basco" in content and "Mae Whitman" in content


def test_movie_page(client: FlaskClient):
    # Check another film in the same way as test_tv_page. This one is a movie
    response = client.get("/film/s5071")
    assert response.status_code == 200

    # Make sure the title, type, and a couple of names are correct
    content = response.data.decode("utf-8")
    assert "Rain Man" in content
    assert "Movie" in content
    assert "Bonnie Hunt" in content and "Lucinda Jenney" in content
    assert "Barry Levinson" in content
