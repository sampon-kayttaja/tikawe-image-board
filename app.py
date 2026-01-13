import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import config
import db

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    error_timer = "<script>setTimeout(function(){ window.location.href = '/register'; }, 2000);</script>"

    if username == "" or password1 == "" or password2 == "":
        return "ERROR: All fields are required!" + error_timer

    if len(username) < 4 or len(username) > 20:
        return "ERROR: Username must be between 4 and 20 characters!" + error_timer

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
        return "ERROR: Password must be at least 6 characters long and include both letters and numbers." + error_timer
        

    if password1 != password2:
        return "ERROR: Passwords do not match." + error_timer

    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "ERROR: Username already in use!" + error_timer

    return "User created successfully! You can now log in." + error_timer

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    
    errormsg =  "Invalid username or password." \
        "<script>setTimeout(function(){ window.location.href = '/'; }, 2000);</script>"

    if username == "" or password == "":   
        return errormsg

    sql = "SELECT COUNT(*) FROM users WHERE username = ?"
    if db.query(sql, [username])[0][0] == 0:
        return errormsg

    sql = "SELECT password_hash FROM users WHERE username = ?"
    password_hash = db.query(sql, [username])[0][0]

    if check_password_hash(password_hash, password):
        session["username"] = username
        return redirect("/")
    else:
        return errormsg

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")
    
