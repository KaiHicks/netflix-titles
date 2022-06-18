from flask import Blueprint, render_template
from flask.wrappers import Response

from app.database import get_db

bp = Blueprint("User", __name__, url_prefix="/user")


@bp.route("/<user_id>", methods=["GET"])
def user_page(user_id: str):
    # Get the user's info
    db = get_db()
    user_row = db.execute(
        "select username from User where user_id_=?", [user_id]
    ).fetchone()
    if not user_row:
        return Response("User does not exist!", status=404)

    # Get the user's comments
    comments = db.execute(
        """
		select comment_id, user_id_, username, film_id, title, date_, body
		from Comment natural join User natural join (
			select film_id, title
			from Film
		)
		where user_id_=?
		order by date_ desc;
		""",
        [user_id],
    ).fetchall()

    return render_template("user.html", user_row=user_row, comments=comments)
