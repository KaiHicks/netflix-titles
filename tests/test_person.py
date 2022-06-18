from urllib.parse import quote_plus

from flask.testing import FlaskClient


def test_person_page_actor(client: FlaskClient):
    """Checks a certain actor's page for accuracy"""
    # Get the page
    response = client.get(f'/person/{quote_plus("Rie Takahashi")}')
    assert response.status_code == 200
    content = response.data.decode("utf-8")

    # Check the name, and a few films that should be there
    assert "Rie Takahashi" in content

    assert "Fate/Grand Order -First Order-" in content
    assert "Revisions" in content
    assert "Sirius the Jaeger" in content
    assert "Teasing Master Takagi-san" in content

    # This actor did not direct anything, so make sure they don't have that section
    # on their page
    assert "Films directed by" not in content


def test_person_page_director(client: FlaskClient):
    """Checks a certain director's page for accuracy"""
    # Get the page
    response = client.get(f'/person/{quote_plus("Quentin Tarantino")}')
    assert response.status_code == 200
    content = response.data.decode("utf-8")

    # Check the name, and a few films that should be there
    assert "Quentin Tarantino" in content

    assert "Kill Bill: Vol. 1" in content
    assert "The Hateful Eight" in content

    assert "Little Nicky" in content
