import functools

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from werkzeug.security import check_password_hash, generate_password_hash

from main.db import get_db
from main.functions import is_valid_email, is_valid_password

from main.functions import CURRENCY

from operator import itemgetter

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        currency = request.form.get("currency")
        symbol = None

        db = get_db()
        error = None
        success = None

        if not username:
            error = "Username field can not be empty."
        elif not email:
            error = "Email field can not be empty."
        elif not is_valid_email(email):
            error = "Email is not valid"
        elif not password:
            error = "Password feild can not be empty."
        elif not is_valid_password(password):
            error = "Password is not valid. Password length should be minimum 8 characters and maximum 18. Password should have at least 1 capital letter, 1 number and 1 special character."
        elif not confirm:
            error = "Confirm password field can not be empty."
        elif confirm != password:
            error = "Passwords should match"
        elif currency not in list(map(itemgetter("name"), CURRENCY)):
            error = "Chosen currency is not available"

        for item in CURRENCY:
            if item["name"] == currency:
                symbol = item["symbol"]

        if error is None:
            try:
                db.execute(
                    "INSERT INTO users (username, email, password, currency, currency_symbol) VALUES (?, ?, ?, ?, ?)",
                    (username, email, generate_password_hash(password),
                     currency, symbol))
                db.commit()
                success = "Account has been created"
                flash(success)
            except db.IntegrityError:
                error = f"{username} username is already taken or account with {email} is already registered."
            else:
                return redirect(url_for("auth.login"))

        flash(error)

    return render_template('auth/register.html', currency=CURRENCY)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        db = get_db()
        error = None
        user = db.execute("SELECT * FROM users WHERE username = ?",
                          (username, )).fetchone()

        if user is None:
            error = "Such user doesn't exist"
        elif not check_password_hash(user["password"], password):
            error = "Incorrect password."

        if error is None:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("index.index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM users WHERE id = ?',
                                  (user_id, )).fetchone()


def login_required(view):

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view
