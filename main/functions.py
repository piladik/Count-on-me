import re
from main.db import get_db

# base categories
CATEGORIES = ["Grocery", "Transport", "Cafe"]


class User():

    def __init__(self, user_id, username, email):
        self.user_id = user_id
        self.username = username
        self.email = email

    def __str__(self):
        information = f"id = {self.user_id}, username = {self.username}, email = {self.email}"
        return information

    def add_card(self, card_name, card_type):
        db = get_db()
        db.execute(
            "INSERT INTO cards (user_id, card_name, card_type) VALUES (?, ?, ?)",
            (self.user_id, card_name, card_type))
        db.commit()

    def delete_card(self, card_id):
        db = get_db()
        db.execute("DELETE FROM cards WHERE user_id = ? and card_id = ?",
                   (self.user_id, card_id))
        db.commit()


class Wallet(User):

    def __init__(self, user_id, username, email):
        super().__init__(user_id, username, email)
        self.db = get_db()
        self.balance = self.db.execute(
            "SELECT SUM(cash) as balance FROM cards WHERE user_id = ?",
            (self.user_id, )).fetchone()["balance"]

    def deposit(self, card_id, amount):
        card_balance = self.db.execute(
            "SELECT cash FROM cards WHERE user_id = ? and card_id = ?",
            (self.user_id, card_id)).fetchone()["cash"]
        self.db.execute("UPDATE cards SET cash = ? WHERE card_id = ?",
                        (card_balance + amount, card_id))
        self.db.commit()
        success = "Money have been added"
        return success

    def withdraw(self, card_id, amount):
        card_balance = self.db.execute(
            "SELECT cash FROM cards WHERE user_id = ? and card_id = ?",
            (self.user_id, card_id)).fetchone()["cash"]

        if card_balance >= amount:
            self.db.execute("UPDATE cards SET cash = ? WHERE card_id = ?",
                            (card_balance - amount, card_id))
            self.db.commit()
            success = "Money have been withdrawn"
            return success
        else:
            error = "Not enough money"
            return error

    def transfer(self, card_from_id, card_to_id, amount):
        card_from_balance = get_card_balance(self.db, self.user_id,
                                             card_from_id)
        card_to_balance = get_card_balance(self.db, self.user_id, card_to_id)

        if amount <= card_from_balance:
            self.db.execute("UPDATE cards SET cash = ? WHERE card_id = ?",
                            (card_to_balance + amount, card_to_id))
            self.db.commit()
            self.db.execute("UPDATE cards SET cash = ? WHERE card_id = ?",
                            (card_from_balance - amount, card_from_id))
            self.db.commit()

    def show_balance_total(self):
        return str(self.balance)

    def get_cards_list(self):
        cards_list = self.db.execute("SELECT * FROM cards WHERE user_id = ?",
                                     (self.user_id, )).fetchall()
        return cards_list


class Purchase(User):

    def __init__(self, user_id, username, email):
        super().__init__(user_id, username, email)
        self.db = get_db()

    def add_purchase(self, category, price, card_id):
        balance = get_card_balance(self.db, self.user_id, card_id)

        # Updates card balance
        balance = balance - price
        self.db.execute(
            "UPDATE cards SET cash = ? WHERE user_id = ? and card_id = ?",
            (balance, self.user_id, card_id))
        self.db.commit()

        # Add purchase into history table
        self.db.execute(
            "INSERT INTO history (user_id, category, price, card_id) VALUES (?, ?, ?, ?)",
            (self.user_id, category, price, card_id))
        self.db.commit()
        success = "Purchase has been added"
        return success

    def delete_purchase(self, purchase_id):
        try:
            card_id = self.db.execute(
                "SELECT card_id FROM history WHERE user_id = ? and purchase_id = ?",
                (self.user_id, purchase_id)).fetchone()["card_id"]
            price = price = self.db.execute(
                "SELECT price FROM history WHERE user_id = ? and purchase_id = ?",
                (self.user_id, purchase_id)).fetchone()["price"]
        except TypeError:
            error = "Access denied."
            return error
        balance = get_card_balance(self.db, self.user_id, card_id)

        # Updates balance
        self.db.execute(
            "UPDATE cards SET cash = ? WHERE user_id = ? and card_id = ?",
            (balance + price, self.user_id, card_id))
        self.db.commit()

        # Deletes from history table
        self.db.execute(
            "DELETE FROM history WHERE user_id = ? and purchase_id = ?",
            (self.user_id, purchase_id))
        self.db.commit()
        success = "Purhase has been deleted"
        return success

    def all_purchase_list(self):
        list = self.db.execute("SELECT * FROM history WHERE user_id = ?",
                               (self.user_id, )).fetchall()
        return list


def get_card_balance(db, user_id, card_id):
    balance = db.execute(
        "SELECT cash FROM cards WHERE user_id = ? and card_id = ?",
        (user_id, card_id)).fetchone()
    return balance["cash"]


#This is email validator function
def is_valid_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if (re.fullmatch(regex, email)):
        return True
    else:
        return False


#This is password validator function
def is_valid_password(password):
    regex = "^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,18}$"

    #Compile regex
    match_re = re.compile(regex)

    #searching regex
    result = re.search(match_re, password)

    if result:
        print("valid")
        return True
    else:
        print("not valid")
        return False