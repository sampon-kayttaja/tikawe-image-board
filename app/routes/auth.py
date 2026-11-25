import secrets
import sqlite3

from flask import Blueprint, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .. import db

bp = Blueprint("auth", __name__)


@bp.route("/new_user")
def new_user():
    return render_template("new_user.html")


@bp.route("/send_user", methods=["POST"])
def send_user():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if username == "":
        return "Username cannot be empty", 400

    if password1 == "" or password2 == "":
        return "Password cannot be empty", 400

    if len(username) < 4:
        return "Username must be at least 4 characters long", 400

    if len(password1) < 8:
        return "Password must be at least 8 characters long", 400

    if password1 != password2:
        return "Passwords do not match", 400

    hashed_password = generate_password_hash(password1)
    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            [username, hashed_password],
        )
    except sqlite3.IntegrityError:
        return "Username already exists", 400

    return redirect("/")


@bp.route("/login")
def login():
    return render_template("login.html")


@bp.route("/send_login", methods=["POST"])
def send_login():
    username = request.form["username"]
    password = request.form["password"]

    sql = "SELECT password_hash FROM users WHERE username = ?"
    password_hash = db.query(sql, [username])

    if password_hash and check_password_hash(password_hash[0][0], password):
        session["username"] = username
        session["user_id"] = db.query(
            "SELECT id FROM users WHERE username = ?", [username]
        )[0]["id"]
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")
    else:
        return "ERROR: Invalid username or password", 401


@bp.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    session.pop("user_id", None)
    session.pop("csrf_token", None)
    return redirect("/login")