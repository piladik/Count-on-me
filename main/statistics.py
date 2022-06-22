from flask import request, url_for, render_template, redirect, Blueprint, session, flash
from main.auth import login_required
from main.db import get_db
from main.functions import User, Wallet, CATEGORIES

bp = Blueprint("statistics", __name__)


@bp.route("/statistics", methods=["GET", "POST"])
@login_required
def statistics():
    return render_template("app/statistics.html")