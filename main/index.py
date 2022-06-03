from flask import request, url_for, render_template, redirect, Blueprint, session
from main.auth import login_required
from main.db import get_db
from main.functions import User, Purchase

bp = Blueprint("index", __name__)


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    db = get_db()
    user_id = session["user_id"]
    user_table = db.execute("SELECT * FROM users where id = ?",
                            (user_id, )).fetchone()
    user = User(user_table["id"], user_table["username"], user_table["email"])
    print(user)
    purchase = Purchase(user_table["id"], user_table["username"],
                        user_table["email"])

    if "add_purchase" in request.form:
        category = request.form.get("category")
        price = request.form.get("price")
        card_id = request.form.get("card_id")

        purchase.add_purchase(category, price, card_id)

    if "delete_purchase" in request.form:
        purchase_id = request.form.get("purchase_id")

        purchase.delete_purchase(purchase_id)

    history = purchase.all_purchase_list()
    for purchase in history:
        print(
            f"Category: {purchase['category']}, Price: {purchase['price']}, Card id: {purchase['card_id']},"
        )
    return render_template("app/index.html")
