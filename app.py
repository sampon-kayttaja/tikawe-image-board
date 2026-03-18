import secrets
import sqlite3
import os
from flask import Flask, abort, jsonify, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import db


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

db.init_db()

@app.route("/")
def index():
    return render_template("index.html")

#user creation and login/logout

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    # Common error timer for all errors

    # Username validation

    if username == "" or password1 == "" or password2 == "":
        return "ERROR: All fields are required!"

    if len(username) < 4 or len(username) > 20:
        return "ERROR: Username must be between 4 and 20 characters!"

    # Password validation

    has_letter = False
    has_number = False

    for a in password1:
        if a.isalpha():
            has_letter = True
            break
    for a in password1:
        if a.isdigit():
            has_number = True
            break

    if not has_letter or not has_number or len(password1) < 6:
        return "ERROR: Password must be at least 6 characters long and include both letters and numbers."
        
    if password1 != password2:
        return "ERROR: Passwords do not match."

    password_hash = generate_password_hash(password1)

    # Insert new user into database

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "ERROR: Username already in use!"

    return render_template("user_created.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    
    errormsg =  "Invalid username or password."

    # Input validation
    # Non-empty fields

    if username == "" or password == "":   
        return errormsg
    
    # Check if user exists

    sql = "SELECT COUNT(*) FROM users WHERE username = ?"
    if db.query(sql, [username])[0][0] == 0:
        return errormsg

    # Verify password and create session

    sql = "SELECT password_hash FROM users WHERE username = ?"
    password_hash = db.query(sql, [username])[0][0]

    if check_password_hash(password_hash, password):
        session["username"] = username
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")
    else:
        return errormsg

@app.route("/logout")
def logout():
    del session["username"]
    del session["csrf_token"]
    return redirect("/")
