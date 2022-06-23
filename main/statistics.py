from flask import request, url_for, render_template, redirect, Blueprint, session, flash
from main.auth import login_required
from main.db import get_db
from main.functions import User, Wallet, CATEGORIES
from datetime import date

bp = Blueprint("statistics", __name__)


@bp.route("/statistics", methods=["GET", "POST"])
@login_required
def statistics():
    db = get_db()
    user_id = session["user_id"]
    dateIsChosen = False

    if request.method == "POST":

        if "select-day" in request.form:
            categoryList = getCategories(db, user_id, dateIsChosen)
            priceList = getPrice(db, user_id, dateIsChosen)

            dayList = getDayList(db, user_id, dateIsChosen)
            totalPerDay = getTotalPerDay(db, user_id, dateIsChosen)

            colorList = []
            for item in dayList:
                colorList.append("#f1c0e8")
            day = getDate(dateIsChosen)
            fday = day.strftime("%B %d")
            today = date.today()
            fmonth = today.strftime("%B")
            table = db.execute(
                "SELECT purchase_id, category, price FROM history WHERE user_id = ? AND date = ? ORDER BY purchase_id",
                (user_id, day)).fetchall()

        else:
            dateIsChosen = True
            categoryList = getCategories(db, user_id, dateIsChosen)
            priceList = getPrice(db, user_id, dateIsChosen)

            dayList = getDayList(db, user_id, dateIsChosen)
            totalPerDay = getTotalPerDay(db, user_id, dateIsChosen)

            colorList = []
            for item in dayList:
                colorList.append("#f1c0e8")

            day = getDate(dateIsChosen)
            today = date.today()
            fday = today.strftime("%B %d")
            fmonth = day.strftime("%B")
            table = db.execute(
                "SELECT purchase_id, category, price FROM history WHERE user_id = ? AND date = ? ORDER BY purchase_id",
                (user_id, today)).fetchall()

    else:
        day = date.today()
        fday = day.strftime("%B %d")
        fmonth = day.strftime("%B")
        table = db.execute(
            "SELECT purchase_id, category, price FROM history WHERE user_id = ? AND date = ? ORDER BY purchase_id",
            (user_id, day)).fetchall()

        categoryList = getCategories(db, user_id, dateIsChosen)
        priceList = getPrice(db, user_id, dateIsChosen)

        dayList = getDayList(db, user_id, dateIsChosen)
        totalPerDay = getTotalPerDay(db, user_id, dateIsChosen)

        colorList = []
        for item in dayList:
            colorList.append("#f1c0e8")

    total = db.execute(
        "SELECT SUM(price) AS price FROM history WHERE user_id = ?",
        (user_id, )).fetchall()

    currency_symbol = db.execute(
        "SELECT currency_symbol FROM users WHERE id = ?",
        (user_id, )).fetchone()

    return render_template("app/statistics.html",
                           categoryList=categoryList,
                           priceList=priceList,
                           dayList=dayList,
                           totalPerDay=totalPerDay,
                           colorList=colorList,
                           table=table,
                           day=fday,
                           month=fmonth,
                           symbol=currency_symbol["currency_symbol"])


# This returns an object of list of categories AND how much money were spent on each category
def sumCategories(db, user_id, dateIsChosen):
    if dateIsChosen == False:
        table = db.execute(
            "SELECT category, SUM(price) as price FROM history WHERE user_id = ? GROUP BY category",
            (user_id, )).fetchall()

    elif dateIsChosen == True:
        year = int(request.form.get("year"))
        month = int(request.form.get("month"))
        day = 1
        chosenMonth = date(year, month, day)
        table = db.execute(
            "SELECT category, SUM(price) as price FROM history WHERE user_id = ? AND strftime('%m', date) = ? GROUP BY category",
            (user_id, chosenMonth.strftime("%m"))).fetchall()
    return table


# This function gets category list from history table
def getCategories(db, user_id, dateIsChosen):
    list = sumCategories(db, user_id, dateIsChosen)
    categoryList = []
    for item in list:
        categoryList.append(item["category"])
    return categoryList


# This function gets price list from history table
def getPrice(db, user_id, dateIsChosen):
    list = sumCategories(db, user_id, dateIsChosen)
    priceList = []
    for item in list:
        priceList.append(item["price"])
    return priceList


# Gets all current month's purchases from history table
def getEachDayTotalSpent(db, user_id, dateIsChosen):
    if dateIsChosen == False:
        today = date.today()
        month = today.strftime("%m")

        list = db.execute(
            "SELECT date, SUM(price) as price FROM history WHERE user_id = ? AND strftime('%m', date) = ? GROUP BY date",
            (user_id, month)).fetchall()

    elif dateIsChosen == True:
        year = int(request.form.get("year"))
        month = int(request.form.get("month"))
        day = 1
        chosenMonth = date(year, month, day)
        print(chosenMonth)
        list = db.execute(
            "SELECT date, SUM(price) as price FROM history WHERE user_id = ? AND strftime('%m', date) = ? GROUP BY date",
            (user_id, chosenMonth.strftime("%m"))).fetchall()

    return list


# This function gets list of days
def getDayList(db, user_id, dateIsChosen):
    dayList = []
    list = getEachDayTotalSpent(db, user_id, dateIsChosen)

    for item in list:
        dateFormated = item["date"].strftime("%d-%m")
        dayList.append(dateFormated)
    return dayList


# This function gets total money spent in each day
def getTotalPerDay(db, user_id, dateIsChosen):
    totalPerDayList = []
    list = getEachDayTotalSpent(db, user_id, dateIsChosen)

    for item in list:
        totalPerDayList.append(item["price"])
    return totalPerDayList


def getDate(dateIsChosen):
    if dateIsChosen == False:
        year = int(request.form.get("year"))
        month = int(request.form.get("month"))
        day = int(request.form.get("day"))
        chosenDate = date(year, month, day)
        print(chosenDate)
    elif dateIsChosen == True:
        year = int(request.form.get("year"))
        month = int(request.form.get("month"))
        day = 1
        chosenDate = date(year, month, day)
    return chosenDate