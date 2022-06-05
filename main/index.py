from locale import currency
from flask import request, url_for, render_template, redirect, Blueprint, session, flash
from main.auth import login_required
from main.db import get_db
from main.functions import User, Purchase, Wallet, CATEGORIES, get_card_balance, total_recent_by_each_category

bp = Blueprint("index", __name__)


@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    db = get_db()
    user_id = session["user_id"]
    user_table = db.execute("SELECT * FROM users where id = ?",
                            (user_id, )).fetchone()
    user = User(user_table["id"], user_table["username"], user_table["email"],
                user_table["currency"], user_table["currency_symbol"])
    purchase = Purchase(user_table["id"], user_table["username"],
                        user_table["email"], user_table["currency"],
                        user_table["currency_symbol"])
    wallet = Wallet(user_table["id"], user_table["username"],
                    user_table["email"], user_table["currency"],
                    user_table["currency_symbol"])
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
                error = "Such purchase doesn't exist."

            if error is None:
                success = purchase.delete_purchase(purchase_id)
                flash(success)
                return redirect(url_for("index.index"))

        if "use_shortcut" in request.form:
            category = request.form.get("category")
            price = request.form.get("price")
            card_id = request.form.get("card_id")

            # check if user has access to selected card
            try:
                card_id = int(card_id)
            except (ValueError):
                error = "Such card doesn't exist."
                flash(error)
                return redirect(url_for("index.index"))

            # if selected card is correct - make sure that input is valid
            try:
                category = category.capitalize()
                price = float(price)
            except (TypeError, ValueError):
                error = "Invalid input"
                flash(error)
                return redirect(url_for("index.index"))

            # if user select card that he doesn't own - flash "access denied."
            try:
                message = purchase.add_purchase(category, price, card_id)
                flash(message)
                return redirect(url_for("index.index"))
            except (TypeError):
                message = "Access denied"
                flash(message)
                return redirect(url_for("index.index"))

        flash(error)

    # Return 10 last purchases from history table
    recent = purchase.show_recent()
    currency_symbol = db.execute(
        "SELECT currency_symbol FROM users WHERE id = ?",
        (user_id, )).fetchone()

    return render_template("app/index.html",
                           categories=CATEGORIES,
                           cards=cards,
                           symbol=currency_symbol["currency_symbol"],
                           recent=recent,
                           recent_by_category=total_recent_by_each_category(
                               db, user_id),
                           shortcuts=wallet.get_shortcuts())
