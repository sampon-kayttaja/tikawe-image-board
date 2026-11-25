import secrets

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    session,
)
from werkzeug.security import check_password_hash, generate_password_hash

import config
import posts as posts
import users as users

app = Flask(__name__)
app.secret_key = config.secret_key


def check_csrf():
    if "csrf_token" not in request.form:
        abort(403)
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.before_request
def require_login():
    if request.endpoint in ["login", "send_login", "new_user", "send_user"]:
        return
    if "username" not in session:
        return redirect("/login")

@app.route("/")
def index():
    search_query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "newest")
    post_rows = posts.get_posts(search_query, sort_by)
    return render_template(
        "index.html",
        posts=post_rows,
        username=session["username"],
        search_query=search_query,
        sort_by=sort_by,
    )


@app.route("/new")
def new():
    return render_template("new.html")


@app.route("/send", methods=["POST"])
def send():
    check_csrf()
    content = request.form["content"]
    title = request.form["title"]
    username = session.get("username")
    file = request.files.get("picture")
    if not title:
        return "Error: Title cannot be empty", 400
    if not content:
        return "Error: Content cannot be empty", 400

    if file is None or not file.filename:
        return "Error: No image uploaded", 400
    if not file.filename.lower().endswith(".jpg"):
        return "Error: Only JPG images are allowed", 400
    image = file.read()
    if len(image) > 100 * 1024:
        return "Error: Image size exceeds 100KB limit", 400

    posts.create_post(title, content, username, image)
    return redirect("/")


@app.route("/post/<int:post_id>")
def post(post_id):
    post_rows = posts.get_post(post_id)
    comments = posts.get_comments(post_id)
    like_count = posts.get_like_count(post_id)
    author = (
        users.get_username_by_id(post_rows[0]["user_id"])
        if post_rows
        else None
    )
    owner = session.get("user_id") == post_rows[0]["user_id"] if post_rows else False

    if post_rows:
        return render_template(
            "post.html",
            post=post_rows[0],
            comments=comments,
            likes=like_count,
            author=author[0]["username"],
            username=session.get("username"),
            owner=owner,
        )
    return "Post not found", 404


@app.route("/post/<int:post_id>/picture")
def post_picture(post_id):
    rows = posts.get_picture(post_id)
    if not rows or rows[0]["picture"] is None:
        abort(404)
    return Response(rows[0]["picture"], mimetype="image/jpeg")


@app.route("/delete/<int:post_id>", methods=["POST"])
def delete(post_id):
    check_csrf()
    post_rows = posts.get_post_user_id(post_id)
    post_user_id = post_rows[0]["user_id"] if post_rows else None
    user_id = session.get("user_id")
    if post_user_id == user_id:
        posts.delete_post(post_id)
    else:
        return "You are not authorized to delete this post", 403
    return redirect("/")


@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    check_csrf()
    content = request.form["content"]
    user_id = session.get("user_id")

    if not content:
        return "Error: Comment content cannot be empty", 400

    posts.create_comment(post_id, content, user_id)
    return redirect(f"/post/{post_id}")


@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    check_csrf()
    comment_rows = posts.get_comment(comment_id)
    comment_user_id = comment_rows[0]["user_id"] if comment_rows else None
    post_id = comment_rows[0]["post_id"] if comment_rows else None
    user_id = session.get("user_id")
    if comment_user_id == user_id:
        posts.delete_comment(comment_id)
    else:
        return "You are not authorized to delete this comment", 403
    return redirect(f"/post/{post_id}")


@app.route("/like/<int:post_id>", methods=["POST"])
def like(post_id):
    check_csrf()
    user_id = session.get("user_id")
    existing_like = posts.get_like(post_id, user_id)
    if not existing_like:
        posts.add_like(post_id, user_id)
    if existing_like:
        posts.remove_like(post_id, user_id)
    return redirect(f"/post/{post_id}")


# User Management

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
    if not users.create_user(username, hashed_password):
        return "Username already exists", 400

    return redirect("/")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/send_login", methods=["POST"])
def send_login():
    check_csrf()
    username = request.form["username"]
    password = request.form["password"]

    user = users.get_user_by_username(username)

    if user and check_password_hash(user[0]["password_hash"], password):
        session["username"] = username
        session["user_id"] = user[0]["id"]
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")
    return "ERROR: Invalid username or password", 401


@app.route("/logout", methods=["POST"])
def logout():
    del session["username"]
    del session["user_id"]
    return redirect("/login")
