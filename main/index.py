from flask import request, url_for, render_template, redirect, Blueprint, session, flash
from main.auth import login_required
from main.db import get_db
from main.functions import User, Purchase, Wallet, CATEGORIES, get_card_balance

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
    wallet = Wallet(user_table["id"], user_table["username"],
                    user_table["email"])
    cards = wallet.get_cards_list()
    error = None
    success = None

    if request.method == "POST":
        if "add_purchase" in request.form:
            category = request.form.get("category")
            price = request.form.get("price")
            card_id = request.form.get("card_id")
            balance = None

            try:
                balance = get_card_balance(db, user_id, card_id)
            except (TypeError, ValueError):
                error = "Please choose the card and input the price."
                flash(error)
                return redirect(url_for("index.index"))

            try:
                price = float(price)
                category = category.capitalize()
            except (TypeError, ValueError, AttributeError):
                error = "Amount should be integer and category can not be empty"
                flash(error)
                return redirect(url_for("index.index"))

            if not price:
                error = "Please type the price."
            elif price == 0:
                error = "Price can not be equal to null."
            elif price > balance:
                error = "Not enough money."
            elif not category:
                error = "Please choose category."
            elif category not in CATEGORIES:
                error = "Such category doesn't exist."

            if error is None:
                success = purchase.add_purchase(category, price, card_id)
                flash(success)
                return redirect(url_for("index.index"))

        if "delete_purchase" in request.form:
            purchase_id = request.form.get("purchase_id")

            if not purchase_id:
                error = "Such purchase doesn't exist"

            if error is None:
                success = purchase.delete_purchase(purchase_id)
                flash(success)
                return redirect(url_for("index.index"))

        flash(error)

    history = purchase.all_purchase_list()
    for purchase in history:
        print(
            f"Category: {purchase['category']}, Price: {purchase['price']}, Card id: {purchase['card_id']},"
        )
    return render_template("app/index.html",
                           categories=CATEGORIES,
                           cards=cards,
                           history=history)
