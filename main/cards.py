from email import message
from typing import Type
from unicodedata import category
from flask import request, url_for, render_template, redirect, Blueprint, session, flash
from main.auth import login_required
from main.db import get_db
from main.functions import User, Wallet, CATEGORIES

bp = Blueprint("cards", __name__)


@bp.route("/cards", methods=["GET", "POST"])
@login_required
def cards():
    db = get_db()
    user_id = session["user_id"]
    user_table = db.execute("SELECT * FROM users where id = ?",
                            (user_id, )).fetchone()
    user = User(user_table["id"], user_table["username"], user_table["email"],
                user_table["currency"], user_table["currency_symbol"])
    wallet = Wallet(user_table["id"], user_table["username"],
                    user_table["email"], user_table["currency"],
                    user_table["currency_symbol"])
    cards = wallet.get_cards_list()
    for card in cards:
        print(f"Name: {card['card_name']}, Card balance: {card['cash']}")
    error = None
    success = None

    if request.method == "POST":
        if "card_create" in request.form:
            card_name = request.form.get("card_name")
            card_type = request.form.get("card_type")

            if not card_name:
                error = "Card name can not be empty"
            elif not card_type:
                error = "Card type can not be empty"

            if error is None:
                user.add_card(card_name, card_type)
                success = "Card has been added"
                flash(success)
                return redirect(url_for("cards.cards"))

        if "card_delete" in request.form:
            card_id = request.form.get("card_id")

            if not card_id:
                error = "Wrong card."

            if error is None:
                user.delete_card(card_id)
                success = "Card has been deleted"
                flash(success)
                return redirect(url_for("cards.cards"))

        if "card_deposit" in request.form:
            card_id = request.form.get("card_id")
            amount = request.form.get("amount")

            if not card_id or not amount:
                error = "Invalid input"

            if error is None:
                try:
                    amount = float(amount)
                    wallet.deposit(card_id, amount)
                    success = "Money have been added"
                    flash(success)
                except (TypeError, ValueError):
                    error = "Amount should be integer"
                else:
                    return redirect(url_for("cards.cards"))

        if "card_withdraw" in request.form:
            card_id = request.form.get("card_id")
            amount = request.form.get("amount")

            if not card_id or not amount:
                error = "Invalid input"

            if error is None:
                try:
                    amount = float(amount)
                except (TypeError, ValueError):
                    error = "Amount should be integer"
                else:
                    ''' this method withdraws money from card. if not enough money returns message "Not enough", otherwise returns "success" '''
                    message = wallet.withdraw(card_id, amount)
                    flash(message)
                    return redirect(url_for("cards.cards"))

        if "card_transfer" in request.form:
            amount = request.form.get("amount")
            card_id_from = request.form.get("card_id_from")
            card_id_to = request.form.get("card_id_to")

            try:
                amount = float(amount)
                card_id_from = int(card_id_from)
                card_id_to = int(card_id_to)
            except (TypeError, ValueError):
                error = "Missing amount or card."
                return redirect(url_for("cards.cards"))
            else:
                message = wallet.transfer(card_id_from, card_id_to, amount)
                flash(message)
                return redirect(url_for("cards.cards"))

        if "card_shortcut" in request.form:
            category = request.form.get("category")
            shortcut_name = request.form.get("name")
            price = request.form.get("price")

            try:
                category = category.capitalize()
                shortcut_name = shortcut_name.capitalize()
                price = float(price)
            except:
                (TypeError, ValueError)
                error = "Invalid input"
                flash(error)
                return redirect(url_for("cards.cards"))
            else:
                message = wallet.create_shortcut(category, shortcut_name,
                                                 price)
                flash(message)
                return redirect(url_for("cards.cards"))

        flash(error)

    return render_template("app/cards.html",
                           cards=cards,
                           categories=CATEGORIES)
