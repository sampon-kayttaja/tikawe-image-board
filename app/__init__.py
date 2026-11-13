from flask import Flask
from flask import redirect, render_template, request
from . import db

app = Flask(__name__)

@app.route("/")
def index():
    posts = db.query("SELECT title, content FROM posts")
    return render_template("index.html", posts=posts)

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    content = request.form["content"]
    title = request.form["title"]
    db.execute("INSERT INTO posts (title, content) VALUES (?, ?)", [title, content])
    return redirect("/")
