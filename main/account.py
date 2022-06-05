from flask import request, url_for, render_template, redirect, Blueprint, session, flash
from werkzeug.security import check_password_hash, generate_password_hash
from main.auth import login_required
from main.db import get_db
from main.functions import is_valid_password, CURRENCY

bp = Blueprint("account", __name__)


@bp.route("/account", methods=["GET", "POST"])
@login_required
def account():
    db = get_db()
    user_id = session["user_id"]
    if request.method == "POST":
        current_password = request.form.get("current_password")
        # get current password from db
        current_password_db = db.execute(
            "SELECT password FROM users WHERE id = ?", (user_id, )).fetchone()
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_new_password")
        error = None
        success = "Password has been changed"

        if not current_password:
            error = "Current password can not be empty."
        elif not check_password_hash(current_password_db["password"],
                                     current_password):
            error = "Password is not correct."
        elif not new_password or is_valid_password(new_password) == False:
            error = "New password is not valid."
        elif not confirm_password:
            error = "Passwords don't match"

        if error is None:
            db.execute("UPDATE users SET password = ?  WHERE id = ?",
                       (generate_password_hash(new_password), user_id))
            db.commit()
            flash(success)
            return (redirect(url_for("account.account")))

        flash(error)

    return render_template("account/account.html", currency=CURRENCY)