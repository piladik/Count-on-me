from email import message
from typing import Type
from flask import request, url_for, render_template, redirect, Blueprint, session, flash
from main.auth import login_required
from main.db import get_db
from main.functions import User, Wallet

bp = Blueprint("cards", __name__)


@bp.route("/cards", methods=["GET", "POST"])
@login_required
def cards():
    db = get_db()
    user_id = session["user_id"]
    user_table = db.execute("SELECT * FROM users where id = ?",
                            (user_id, )).fetchone()
    user = User(user_table["id"], user_table["username"], user_table["email"])
    print(user)
    wallet = Wallet(user_table["id"], user_table["username"],
                    user_table["email"])
    print(wallet.show_balance_total())
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

        # TODO if "card_transfer" in request.form

        flash(error)

    return render_template("app/cards.html")