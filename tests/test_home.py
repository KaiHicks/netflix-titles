import pytest

from flask.testing import FlaskClient


def test_home(client: FlaskClient):
    """
    Checks that a request to '/' has status code 200
    """
    response = client.get("/")
    assert response.status_code == 200


def test_num_films(client: FlaskClient):
    """
    Makes three requests to / with each sorting method. Ensures that they all
    have status code 200 and the same number of films listed. Also, it checks
    that at least 10 films are found.
    """
    featured = client.get("/", query_string={"sort": "feature"})
    titles = client.get("/", query_string={"sort": "title"})
    released = client.get("/", query_string={"sort": "release_year"})

    # The responses suceeded
    assert featured.status_code == 200
    assert titles.status_code == 200
    assert released.status_code == 200

    token = "<!-- :filmtile: -->"
    print(featured.data.decode("utf-8"))

    # All sorts have the same number of films
    assert (
        featured.data.decode("utf-8").count(token)
        == titles.data.decode("utf-8").count(token)
        == released.data.decode("utf-8").count(token)
    )

    # They also have at least ten (it should be more like 50, but whatever)
    assert featured.data.decode("utf-8").count(token) > 10


def test_titles_sorted(client: FlaskClient):
    """
    Requests / with sorting method 'title' and checks that the titles are
    indeed sorted.
    """
    response = client.get("/", query_string={"sort": "title"})
    # Parse the HTML and get the titles
    titles = [
        tile.a.div.h5.text.strip()
        for tile in response.html.find_all("div", {"class": "filmtile"})
    ]

    # Check that the titles are sorted
    last_tile = titles[0]
    for tile in titles[1:]:
        assert tile > last_tile
        last_tile = tile


@pytest.mark.parametrize(("sort",), (("",), ("titles",), ("something",)))
def test_improper_sorting(client: FlaskClient, sort):
    """Checks that requesting an invalid sorting method returns a 400"""
    response = client.get("/", query_string={"sort": sort})
    assert response.status_code == 400
