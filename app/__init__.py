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
    if session.get("username") is None and request.endpoint not in ["login", "send_login", "new_user", "send_user"]:
        return redirect("/login")

# HOME PAGE

@app.route("/")
def index():
    search_query = request.args.get("q", "").strip()
    sort_orders = {
        "newest": "posts.created_at DESC, posts.id DESC",
        "oldest": "posts.created_at ASC, posts.id ASC",
        "most_liked": "like_count DESC, posts.created_at DESC, posts.id DESC",
    }
    sort_by = request.args.get("sort", "newest")
    if sort_by not in sort_orders:
        sort_by = "newest"

    sql = """
        SELECT posts.id, posts.title, posts.content,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
        FROM posts
    """
    params = []
    if search_query:
        sql += " WHERE posts.title LIKE ?"
        params.append(f"%{search_query}%")
    sql += f" ORDER BY {sort_orders[sort_by]}"
    posts = db.query(sql, params)
    return render_template(
        "index.html",
        posts=posts,
        username=session["username"],
        search_query=search_query,
        sort_by=sort_by,
    )

# NEW POST

@app.route("/new")
def new():
    return render_template("new.html")

@app.route("/send", methods=["POST"])
def send():
    content = request.form["content"]
    title = request.form["title"]
    username = session.get("username")
    db.execute("INSERT INTO posts (title, content, user_id) VALUES (?, ?, (SELECT id FROM users WHERE username = ?))", [title, content, username])
    return redirect("/")

# VIEW POST

@app.route("/post/<int:post_id>")
def post(post_id):
    post = db.query("SELECT id, title, content, user_id FROM posts WHERE id = ?", [post_id])
    comments = db.query("SELECT comments.id, comments.post_id, comments.content, comments.user_id, users.username AS author FROM comments JOIN users ON comments.user_id = users.id WHERE comments.post_id = ?", [post_id])
    likes = db.query("SELECT COUNT(*) as like_count FROM likes WHERE post_id = ?", [post_id])
    like_count = likes[0][0]
    author = db.query("SELECT username FROM users WHERE id = ?", [post[0]["user_id"]]) if post else None
    owner = session.get("user_id") == post[0]["user_id"] if post else False
    
    if post:
        return render_template("post.html", post=post[0], comments=comments, likes=like_count, author=author[0]["username"] if author else None, username=session.get("username"), owner=owner)
    return "Post not found", 404

@app.route("/delete/<int:post_id>", methods=["POST"])
def delete(post_id):
    post = db.query("SELECT user_id FROM posts WHERE id = ?", [post_id])
    post_user_id = post[0]["user_id"] if post else None
    user_id = session.get("user_id")
    if post_user_id == user_id:
        db.execute("DELETE FROM posts WHERE id = ?", [post_id])
        db.execute("DELETE FROM comments WHERE post_id = ?", [post_id])
        db.execute("DELETE FROM likes WHERE post_id = ?", [post_id])
    else:
        return "You are not authorized to delete this post", 403
    return redirect("/")

@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    content = request.form["content"]
    user_id = session.get("user_id")
    db.execute("INSERT INTO comments (post_id, content, user_id) VALUES (?, ?, ?)", [post_id, content, user_id])
    return redirect(f"/post/{post_id}")

@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    comment = db.query("SELECT user_id, post_id FROM comments WHERE id = ?", [comment_id])
    comment_user_id = comment[0]["user_id"] if comment else None
    post_id = comment[0]["post_id"] if comment else None
    user_id = session.get("user_id")
    if comment_user_id == user_id:
        db.execute("DELETE FROM comments WHERE id = ?", [comment_id])
    else:
        return "You are not authorized to delete this comment", 403
    return redirect(f"/post/{post_id}")

@app.route("/like/<int:post_id>", methods=["POST"])
def like(post_id):
    user_id = session.get("user_id")
    existing_like = db.query("SELECT * FROM likes WHERE post_id = ? AND user_id = ?", [post_id, user_id])
    if not existing_like:
        db.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", [post_id, user_id])
    if existing_like:
        db.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", [post_id, user_id])
    return redirect(f"/post/{post_id}")

# USER CREATION

@app.route("/new_user")
def new_user():
    return render_template("new_user.html")

@app.route("/send_user", methods=["POST"])
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
        db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", [username, hashed_password])
    except sqlite3.IntegrityError:
        return "Username already exists", 400

    return redirect("/")

# LOGIN AND LOGOUT

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/send_login", methods=["POST"])
def send_login():
    username = request.form["username"]
    password = request.form["password"]
    
    sql = "SELECT password_hash FROM users WHERE username = ?"
    password_hash = db.query(sql, [username])

    if password_hash and check_password_hash(password_hash[0][0], password):
        session["username"] = username
        session["user_id"] = db.query("SELECT id FROM users WHERE username = ?", [username])[0]["id"]
        return redirect("/")
    else:
        return "ERROR: Invalid username or password", 401

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")