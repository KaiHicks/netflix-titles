from flask import Blueprint, request
from flask.templating import render_template
from flask.wrappers import Response

from app.film import ArgumentValidationError, get_films

bp = Blueprint("home", __name__)


@bp.route("/")
def home() -> str:
    # Get the sorting method and default to "feature" if none is specified
    sort = request.args.get("sort", "feature")
    try:
        films = get_films(order=sort)
    except ArgumentValidationError:
        return Response("Invalid request", status=400)
    return render_template("home.html", films=films, sort=sort)
