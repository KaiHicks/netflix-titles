import json
import secrets
from base64 import b64decode, b64encode
from hashlib import blake2b
from sys import modules
from time import time as now
from typing import NamedTuple, Optional, TypeAlias

from flask import Blueprint, redirect, request, session
from flask.helpers import url_for
from flask.templating import render_template
from flask.wrappers import Response
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from sortedcontainers import SortedDict

from app.database import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")

CHALLENGE_TIME_LIM = 30.0

this = modules[__name__]

# Typing
SessId: TypeAlias = str
Challenge: TypeAlias = str


class ChallengeInfo(NamedTuple):
    challenge: str
    sess_id: str
    exp_time: float


# Maps challenges to session ids and expiration times
this.active_challenges = dict()
# Maps the time the challenge expires to challenges
# We are mapping this way to make it easier to discard all expired challenges
# and discard completed challenges
this.challenge_expires = SortedDict()

# maps sess_id to user_id
this.sessions = dict()


def sess_id() -> SessId:
    """Gets the session id of the current user. If the current user has no session id,
    one is generated and returned

    Returns:
            str: A URL-safe string representing the session id
    """
    if "sess_id" not in session:
        session["sess_id"] = secrets.token_urlsafe(256 // 8)

    return session["sess_id"]


def pop_challenge(
    challenge: Optional[Challenge] = None, exp_time: Optional[float] = None
) -> ChallengeInfo:
    """Removes and returns a challenge from the active challenges. If only one argument
    is provided, the other will be inferred. If neither is provided, a KeyError will be
    raised.

    Args:
        challenge (Optional[Challenge], optional): The challenge string to remove.
        exp_time (Optional[float], optional): The time the challenge expires.

    Returns:
        ChallengeInfo: Information about the challenge that was removed.
    """
    # Infer the challenge from the exp_time if it is not provided
    if challenge is None:
        challenge = this.challenge_expires[exp_time]
    # Get the challenge info and remove it from the expiration list
    sess_id, exp_time = this.active_challenges.pop(challenge)
    del this.challenge_expires[exp_time]

    return ChallengeInfo(challenge, sess_id, exp_time)


def expire_challenges() -> None:
    """Invalidates all challenges that are past their expirations"""
    # Get the number of challenges that are expired
    n_challenges = this.challenge_expires.bisect(now())
    # Iterate over all the expiry times
    # We cannot use .items()  because of the way that SortedDict is implemented
    # The reason I am converting this into a list instead of just using the
    # iterable is because I will be modifying challenge_expires
    for exp_time in list(this.challenge_expires.islice(0, n_challenges)):
        # Remove these challenges from everything
        pop_challenge(exp_time=exp_time)


def generate_challenge(time_lim: float = CHALLENGE_TIME_LIM) -> Challenge:
    """
    Generates, registers, and returns a new authentication challenge.

    Args:
        time_lim (float, optional): Sets the expiration for the challenge. Defaults to
        CHALLENGE_TIME_LIM.

    Returns:
        str: The new challenge.
    """
    expire_challenges()

    challenge = f"authchallenge_{secrets.token_urlsafe(256//8)}"
    exp_time = now() + time_lim
    this.active_challenges[challenge] = (sess_id(), exp_time)
    this.challenge_expires[exp_time] = challenge

    return challenge


def complete_challenge(signature_hex: str, pub_key_hex: str) -> bool:
    """
    Validates the challenge-response and returns True if it was successfully completed.
    This function also deregisters the challenge.

    Args:
        signature_hex (str): The response to the challenge
        pub_key_hex (str): The user's public key. Must be read from the DB, and not
            provided by the user

    Returns:
        bool: True if the challenge was completed correctly
    """
    # First, deregister any expired challenges. This will invalidate this
    # challenge-response if it is expired.
    expire_challenges()

    # Construct the key object. We cannot simply get the key object as a parameter since
    # it will be pulled from the database
    pub_key = VerifyKey(bytes.fromhex(pub_key_hex))
    try:
        # Check the signature
        challenge = pub_key.verify(bytes.fromhex(signature_hex))
        challenge = str(challenge, "utf-8")
    except BadSignatureError:
        return False

    # Now that we have verified the signature, we need to deregister the challenge and
    # make sure that its session id corresponds to the current user's
    challenge_info = pop_challenge(challenge=challenge)
    if challenge_info.sess_id != sess_id():
        # The challenge was created by someone other than who is trying to complete it!
        # We don't want this to have actually deregistered the challenge, as that could
        # give rise to a DOS attack preventing logins.
        # Register the challenge again, and make sure it expires at the exact same time
        # that it would have.
        this.challenge_expires[challenge_info.exp_time] = challenge_info.challenge
        this.active_challenges[challenge_info.challenge] = (
            sess_id(),
            challenge_info.exp_time,
        )
        return False

    return True


def username_taken(username: str) -> bool:
    db = get_db()
    user = db.execute("select * from User where username like ?", [username]).fetchall()
    return bool(user)


def login_user(user_id: str) -> None:
    logout_user()

    # Add the session to the db
    db = get_db()
    db.execute(
        """
            insert into Sess(sess_id, user_id_)
            values(?, ?)
        """,
        [sess_id(), user_id],
    )
    db.commit()

    # Add it to the known sessions
    this.sessions[sess_id()] = user_id


def logout_user() -> None:
    # Remove the session from the db
    db = get_db()
    db.execute("delete from Sess where sess_id=?", [sess_id()])
    db.commit()

    # Remove the session from the known sessions
    if sess_id() in this.sessions:
        del this.sessions[sess_id()]

    # Remove the session cookie
    del session["sess_id"]


def get_sess_info():
    db = get_db()
    return db.execute(
        "select * from Sess natural join User where sess_id=?", [sess_id()]
    ).fetchone()


# routes


@bp.route("/", methods=["GET"])
def auth_page():
    return render_template("/authentication/auth.html")


@bp.route("/register", methods=["POST"])
def register():
    # Get username and password
    try:
        if not request.args:
            data = json.loads(str(request.data, "utf-8"))
        else:
            data = request.args
        username = data["username"]
        # This is not actually the password, it is KDF(password)
        password = b64decode(data["password"])
    except KeyError:
        return Response("Incorrect args sent by client", status=400)
    except json.decoder.JSONDecodeError:
        print(request.data)
        return Response("Invalid data - must be json", status=406)

    if username_taken(username):
        return Response("Username  is taken", status=403)

    # Compute a salted hash of the password
    salt = secrets.token_bytes(128 // 8)
    # We are using blake2b instead of a KDF because the password was already fed through
    # a KDF. So, in effect the password is double-hashed. The first hash (KDF) prevents
    # the server from knowing the password as it is never transmitted. The second hash
    # here ensures that the database does contain everything one would need to
    # authenticate themselves as another user.
    hash_ = blake2b(salt=salt)
    hash_.update(password)
    pass_hash = str(b64encode(hash_.digest()), "utf-8")

    # Add the new user to the DB
    db = get_db()
    db.execute(
        """
            insert into
            User(user_id_, username, pass_hash, pass_salt)
            values(?, ?, ?, ?)
        """,
        [
            f"userid_{secrets.token_urlsafe(256//8)}",
            username,
            pass_hash,
            b64encode(salt),
        ],
    )
    db.commit()

    return Response("Successfully registered", status=200)


@bp.route("/login", methods=["POST"])
def login():
    # Get the username and hashed password
    try:
        if not request.args:
            data = json.loads(str(request.data, "utf-8"))
        else:
            data = request.args
        username = data["username"]
        password = b64decode(data["password"])
    except KeyError:
        return Response("Incorrect args sent by client", status=400)
    except json.decoder.JSONDecodeError:
        print(request.data)
        return Response("Invalid data - must be json", status=406)

    # If the username is not taken, then the username must not exist
    if not username_taken(username):
        return Response("Incorrect username", status=404)

    # Get the user's info from the DB
    db = get_db()
    user_row = db.execute(
        "select * from User where username like ?", [username]
    ).fetchone()

    # -- WARNING --
    # THIS PORTION IS VERY SENSITIVE
    hash_ = blake2b(salt=b64decode(user_row["pass_salt"]))
    hash_.update(password)
    # It is EXTREMELY IMPORTANT that we encode the given password instead of
    # decoding the pass_hash from the db. I doubt that b64encode and b64decode
    # are timing-safe, and doing this incorrectly could lead to a timing attack.
    # This could leak the hashed password of a user.
    password = str(b64encode(hash_.digest()), "utf-8")

    # DO NOT CHANGE THIS TO == OR ANYTHING SIMILAR, we must use compare_digest for
    # timing safety.
    if secrets.compare_digest(password, user_row["pass_hash"]):
        login_user(user_row["user_id_"])
        return redirect(url_for("home.home"))
    else:
        return Response("Incorrect username or password", status=401)


@bp.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("home.home"))
