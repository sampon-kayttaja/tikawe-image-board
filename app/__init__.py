from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import config
import sqlite3

from . import db

app = Flask(__name__)
app.secret_key = config.secret_key

@app.before_request
def before_request():
    if session.get("username") is None and request.endpoint not in ["login", "sendLogin", "newUser", "sendUser"]:
        return redirect("/login")

@app.route("/")
def index():
    posts = db.query("SELECT id, title, content FROM posts")
    return render_template("index.html", posts=posts, username=session["username"])

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    content = request.form["content"]
    title = request.form["title"]
    db.execute("INSERT INTO posts (title, content) VALUES (?, ?)", [title, content])
    return redirect("/")

@app.route("/post/<int:post_id>")
def post(post_id):
    post = db.query("SELECT id, title, content FROM posts WHERE id = ?", [post_id])
    comments = db.query("SELECT id, post_id, content FROM comments WHERE post_id = ?", [post_id])
    if post:
        return render_template("post.html", post=post[0], comments=comments, username=session.get("username"))
    return "Post not found", 404

@app.route("/newUser")
def newUser():
    return render_template("newUser.html")

@app.route("/sendUser", methods=["POST"])
def sendUser():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if password1 != password2:
        return "Passwords do not match", 400

    hashed_password = generate_password_hash(password1)
    try:
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", [username, hashed_password])
    except sqlite3.IntegrityError:
        return "Username already exists", 400

    return redirect("/")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/sendLogin", methods=["POST"])
def sendLogin():
    username = request.form["username"]
    password = request.form["password"]
    
    sql = "SELECT password_hash FROM users WHERE username = ?"
    password_hash = db.query(sql, [username])

    if password_hash and check_password_hash(password_hash[0][0], password):
        session["username"] = username
        return redirect("/")
    else:
        return "ERROR: Invalid username or password", 401

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")