import re
from main.db import get_db

# base categories
CATEGORIES = ["Grocery", "Transport", "Cafe"]
CURRENCY = [{"name": "EUR", "symbol": "€"}, {"name": "USD", "symbol": "$"}]


class User():

    def __init__(self, user_id, username, email, currency_name,
                 currency_symbol):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.currency = currency_name
        self.symbol = currency_symbol

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

    def __init__(self, user_id, username, email, currency_name,
                 currency_symbol):
        super().__init__(user_id, username, email, currency_name,
                         currency_symbol)
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
        try:
            card_from_balance = get_card_balance(self.db, self.user_id,
                                                 card_from_id)
            card_to_balance = get_card_balance(self.db, self.user_id,
                                               card_to_id)
        except TypeError:
            message = "Access denied"
            return message
        else:
            if amount <= card_from_balance:
                self.db.execute("UPDATE cards SET cash = ? WHERE card_id = ?",
                                (card_to_balance + amount, card_to_id))
                self.db.commit()
                self.db.execute("UPDATE cards SET cash = ? WHERE card_id = ?",
                                (card_from_balance - amount, card_from_id))
                self.db.commit()
                message = "Money have been successfully transfered."
                return message
            else:
                message = "Not enough money"
                return message

    def create_shortcut(self, category, shortcut_name, price):
        self.db.execute(
            "INSERT INTO shortcuts (user_id, category, name, price) VALUES (?, ?, ?, ?)",
            (self.user_id, category, shortcut_name, price))
        self.db.commit()
        success = "Shortcut has been created"
        return success

    def get_shortcuts(self):
        shortcuts = self.db.execute(
            "SELECT * FROM shortcuts WHERE user_id = ?",
            (self.user_id, )).fetchall()
        if len(shortcuts) == 0:
            return 0
        else:
            return shortcuts

    def show_balance_total(self):
        return str(self.balance)

    def get_cards_list(self):
        cards_list = self.db.execute("SELECT * FROM cards WHERE user_id = ?",
                                     (self.user_id, )).fetchall()
        return cards_list

    def hasCards(self):
        db = self.db.execute("SELECT * FROM cards WHERE user_id = ?",
                             (self.user_id, )).fetchall()
        if len(db) > 0:
            return True
        else:
            return False


class Purchase(User):

    def __init__(self, user_id, username, email, currency_name,
                 currency_symbol):
        super().__init__(user_id, username, email, currency_name,
                         currency_symbol)
        self.db = get_db()

    def add_purchase(self, category, price, card_id):
        print("I work")
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

    def show_recent(self):
        list = self.db.execute(
            "SELECT * FROM history WHERE user_id = ? ORDER BY purchase_id DESC LIMIT 10",
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


# TODO Redesign so that I don't have to type categories manually
def total_recent_by_each_category(db, user_id):
    operations = db.execute(
        "SELECT purchase_id, category, price, date FROM history WHERE user_id = ? ORDER BY purchase_id DESC LIMIT 10",
        (user_id, )).fetchall()

    totalSpent = float(0)
    cafe = float(0)
    transport = float(0)
    grocery = float(0)

    for operation in operations:
        totalSpent = operation["price"] + totalSpent
        if operation["category"] == "Cafe":
            cafe = operation["price"] + cafe
        elif operation["category"] == "Transport":
            transport = operation["price"] + transport
        elif operation["category"] == "Grocery":
            grocery = operation["price"] + grocery

    cafe = toPercent(cafe, totalSpent)
    transport = toPercent(transport, totalSpent)
    grocery = toPercent(grocery, totalSpent)

    list = {
        "total": totalSpent,
        "cafe": cafe,
        "transport": transport,
        "grocery": grocery
    }
    return list


# percentFormat
def toPercent(part, whole):
    if part == 0 and whole == 0:
        return 0
    else:
        percentage = round(part / whole * 100, 2)
        return str(percentage) + " %"


# return True if user has any card