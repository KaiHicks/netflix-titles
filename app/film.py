import secrets
from datetime import datetime
from sqlite3 import Cursor

from flask import Blueprint, request
from flask.helpers import url_for
from flask.templating import render_template
from flask.wrappers import Response
from werkzeug.utils import redirect

from app.auth import get_sess_info

from .database import get_db

bp = Blueprint("film", __name__, url_prefix="/film")


class ArgumentValidationError(ValueError):
    ...


def get_films(order: str = "feature", limit: int = 50) -> Cursor:
    """
    Gets a list of films from the db.

    Params:
            limit:int - The number of entries to fetch
            order:str - The order by which to sort the results. Must be 'feature',
                    'title', or 'release_year'.

            If the limit is not an integer or the order is invalid, an
            ArgumentValidationError will be raised to curtail any possible sql
            injection.
    """

    # Validate
    if order not in {"feature", "title", "release_year"} or not isinstance(limit, int):
        raise ArgumentValidationError()

    db = get_db()

    films = db.execute(f"select * from Film order by {order} limit ?", [limit])
    return films


@bp.route("/<film_id>", methods=["GET"])
def film_page(film_id) -> str:
    """
    Renders the page for the given film_id. Film_id must be of the form 's#`
    where # is a base-10 number. If film_id is not in that form, a 400-response
    will be returned.
    """

    # Validate
    if not film_id.startswith("s") or not film_id[1:].isdigit():
        return Response("Bad film id", status=400)

    if request.method == "GET":
        # Get the film
        db = get_db()
        film_row = db.execute(
            f'select * from Film where film_id="{film_id}"'
        ).fetchone()
        if not film_row:
            return Response(status=404)

        # Tags
        tags = db.execute(
            f"select genre_name from Listed where " f'film_id="{film_id}"'
        ).fetchall()
        tags = [t["genre_name"] for t in tags]

        # Directors
        directors = db.execute(
            f"select person_name from Directed where " f'film_id="{film_id}"'
        ).fetchall()
        directors = [d["person_name"] for d in directors]

        # Cast
        cast = db.execute(
            f"select person_name from Acted where " f'film_id="{film_id}"'
        ).fetchall()
        cast = [c["person_name"] for c in cast]

        # Comments
        comments = db.execute(
            """
			select comment_id, user_id_, username, film_id, title, date_, body
			from Comment natural join User natural join (
				select film_id, title
				from Film
				where film_id=?
			)
			order by date_ desc;
			""",
            [film_id],
        ).fetchall()

        return render_template(
            "films/film.html",
            film_row=film_row,
            tags=tags,
            directors=directors,
            cast=cast,
            comments=comments,
        )
    else:
        return Response(status=300)


@bp.route("/<film_id>/comment", methods=["POST"])
def submit_comment(film_id: str):
    # Get the comment
    try:
        body = request.form["comment"]
    except KeyError:
        return Response("Incorrect args sent by client", status=400)

    # Check if logged in
    sess_info = get_sess_info()
    if not sess_info:
        return Response("You must be logged in to do that!", status=401)

    # Create a comment id and insert the comment into the db
    # We don't *really* need this to be cryptographically safe, but I don't want to deal
    # with making sure it's unique, and the standard random modules only have 64 bits
    # of entropy
    comment_id = secrets.token_urlsafe(256 // 8)
    db = get_db()
    db.execute(
        """
			insert into Comment values(?, ?, ?, ?, ?)
		""",
        [comment_id, sess_info["user_id_"], film_id, str(datetime.now()), body],
    )
    db.commit()

    return redirect(f'{url_for("film.film_page", film_id=film_id)}#{comment_id}')


@bp.route("/<film_id>/comment/<comment_id>/edit", methods=["POST"])
def edit_comment(film_id, comment_id):
    try:
        body = request.form["comment"]
    except KeyError:
        return Response("Incorrect args sent by client", status=400)

    sess_info = get_sess_info()
    if not sess_info:
        return Response("You must be logged in to do that!", status=401)

    # Get the comment from the db
    db = get_db()
    cursor = db.execute(
        "select user_id_ from Comment where comment_id=? and film_id=?",
        [comment_id, film_id],
    )
    comment_row = cursor.fetchone()
    cursor.close()
    if not comment_row:
        return Response("No such comment", status=404)

    # Make sure the logged in user is the author of the comment
    if comment_row["user_id_"] != sess_info["user_id_"]:
        return Response("You cannot edit other users' comments", status=403)

    # We are specifying the user_id again as a sanity check just in case something
    # went wrong above.
    cursor = db.execute(
        """
			update Comment set body=?
			where film_id=? and comment_id=? and user_id_=?
		""",
        [body, film_id, comment_id, sess_info["user_id_"]],
    )
    db.commit()
    cursor.close()

    return redirect(f'{url_for("film.film_page", film_id=film_id)}#{comment_id}')


@bp.route("/<film_id>/comment/<comment_id>/delete", methods=["POST"])
def delete_comment(film_id, comment_id):
    sess_info = get_sess_info()
    if not sess_info:
        return Response("You must be logged in to do that!", status=401)

    # I could just delete all comments with the given film_id, comment_id, and
    # user_id, but then if it doesn't delete anything, I won't know if it's
    # because the comment doesn't exist or if it's because the user_id is wrong
    # Get the comment
    db = get_db()
    cursor = db.execute(
        "select user_id_ from Comment where comment_id=? and film_id=?",
        [comment_id, film_id],
    )
    comment_row = cursor.fetchone()
    cursor.close()
    # Check if the comment even exists
    if not comment_row:
        return Response("No such comment", status=404)

    # Make sure the logged in user authored the comment
    if comment_row["user_id_"] != sess_info["user_id_"]:
        return Response("You cannot delete other users' comments", status=403)

    # We are specifying the user_id again as a sanity check just in case something
    # went wrong above.
    cursor = db.execute(
        """
			delete from Comment
			where film_id=? and comment_id=? and user_id_=?
		""",
        [film_id, comment_id, sess_info["user_id_"]],
    )
    db.commit()
    cursor.close()

    return redirect(url_for("film.film_page", film_id=film_id))
