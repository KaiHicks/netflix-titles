from urllib.parse import unquote_plus

from flask import Blueprint, escape
from flask.templating import render_template
from flask.wrappers import Response

from .database import get_db

bp = Blueprint("person", __name__, url_prefix="/person")


@bp.route("/<name>", methods=["GET"])
def person_page(name):
    db = get_db()
    # Convert the name from a url-safe encoding to its actual value
    name = unquote_plus(name)

    # Get everything they directed
    directed = db.execute(
        "select * from Film natural join Directed where " "person_name = ?", [name]
    ).fetchall()

    # Get everything they acted in
    acted = db.execute(
        "select * from Film natural join Acted where " "person_name = ?", [name]
    ).fetchall()

    if not directed and not acted:
        # If they did nothing, then how did they make it into the database?
        return Response("We don't know who this person is", status=404)
    else:
        return render_template(
            "films/person.html", name=escape(name), directed=directed, acted=acted
        )
