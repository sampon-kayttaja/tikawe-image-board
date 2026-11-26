import secrets

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    flash,
    request,
    session,
)
from werkzeug.security import check_password_hash, generate_password_hash

import config
import posts
import users

app = Flask(__name__)
app.secret_key = config.secret_key

TOPICS = ("Nature", "Art", "Travel", "Food", "Sports", "Music", "Fashion", "Other")

def check_csrf():
    if "csrf_token" not in request.form:
        abort(403)
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.before_request
def require_login():
    if request.endpoint not in ["login", "send_login", "new_user", "send_user"] and session.get("username") is None:
        return redirect("/login")

@app.route("/")
@app.route("/<int:page>")
def index(page=1):
    search_query = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "newest")
    topic_filter = request.args.get("topic", "").strip()

    if topic_filter not in TOPICS:
        topic_filter = ""

    page_size = 10
    posts_amount = posts.get_posts_count(search_query, topic_filter)
    pages_amount = max(1, (posts_amount + page_size - 1) // page_size)

    if page < 1:
        return redirect("/")
    if page > pages_amount:
        return redirect(f"/{pages_amount}")

    post_rows = posts.get_posts(
        search_query,
        sort_by,
        topic=topic_filter,
        page=page,
        page_size=page_size,
    )
    return render_template(
        "index.html",
        posts=post_rows,
        username=session["username"],
        search_query=search_query,
        sort_by=sort_by,
        topic_filter=topic_filter,
        topics=TOPICS,
        page=page,
        pages_amount=pages_amount,
    )

@app.route("/new")
def new():
    return render_template("new.html", topics=TOPICS)

@app.route("/send", methods=["POST"])
def send():
    check_csrf()
    content = request.form["content"]
    title = request.form["title"]
    username = session.get("username")
    file = request.files.get("picture")
    topic = request.form.get("topic", "").strip()
    content = content.strip()
    title = title.strip()

    if not title:
        flash("Error: Title cannot be empty", "error")
        return redirect("/new")
    if len(title) > 100:
        flash("Error: Title cannot exceed 100 characters", "error")
        return redirect("/new")
    if not content:
        flash("Error: Content cannot be empty", "error")
        return redirect("/new")
    if len(content) > 1000:
        flash("Error: Content cannot exceed 1000 characters", "error")
        return redirect("/new")
    if topic not in TOPICS:
        flash("Error: Please select a valid topic", "error")
        return redirect("/new")
    if file is None or not file.filename:
        flash("Error: No image uploaded", "error")
        return redirect("/new")
    if not file.filename.lower().endswith(".jpg"):
        flash("Error: Only JPG images are allowed", "error")
        return redirect("/new")
    if file.mimetype != "image/jpeg":
        flash("Error: Only JPG images are allowed", "error")
        return redirect("/new")
    image = file.read()
    if len(image) > 100 * 1024:
        flash("Error: Image size exceeds 100KB limit", "error")
        return redirect("/new")

    posts.create_post(title, content, topic, username, image)
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
    flash("Post not found", "error")
    return redirect("/")

@app.route("/post/<int:post_id>/picture")
def post_picture(post_id):
    rows = posts.get_picture(post_id)
    if not rows or rows[0]["picture"] is None:
        abort(404)
    return Response(rows[0]["picture"], mimetype="image/jpeg")

@app.route("/edit_post/<int:post_id>")
def edit(post_id):
    post_rows = posts.get_post(post_id)
    if not post_rows:
        flash("Post not found", "error")
        return redirect("/")
    post_user_id = post_rows[0]["user_id"]
    user_id = session.get("user_id")
    if post_user_id != user_id:
        flash("You are not authorized to edit this post", "error")
        return redirect(f"/post/{post_id}")
    return render_template("edit_post.html", post=post_rows[0])

@app.route("/update_post/<int:post_id>", methods=["POST"])
def update_post(post_id):
    check_csrf()
    post_rows = posts.get_post(post_id)
    if not post_rows:
        flash("Post not found", "error")
        return redirect("/")
    post_user_id = post_rows[0]["user_id"]
    user_id = session.get("user_id")
    if post_user_id != user_id:
        flash("You are not authorized to edit this post", "error")
        return redirect(f"/post/{post_id}")

    title = request.form["title"]
    content = request.form["content"]
    topic = request.form.get("topic", "").strip()

    if not title:
        flash("Error: Title cannot be empty", "error")
        return redirect(f"/edit_post/{post_id}")
    if len(title) > 100:
        flash("Error: Title cannot exceed 100 characters", "error")
        return redirect(f"/edit_post/{post_id}")
    if not content:
        flash("Error: Content cannot be empty", "error")
        return redirect(f"/edit_post/{post_id}")
    if len(content) > 1000:
        flash("Error: Content cannot exceed 1000 characters", "error")
        return redirect(f"/edit_post/{post_id}")
    if topic not in TOPICS:
        flash("Error: Please select a valid topic", "error")
        return redirect(f"/edit_post/{post_id}")

    posts.update_post(post_id, title, content, topic)
    return redirect(f"/post/{post_id}")

@app.route("/delete/<int:post_id>", methods=["POST"])
def delete(post_id):
    check_csrf()
    post_rows = posts.get_post_user_id(post_id)
    if not post_rows:
        flash("Post not found", "error")
        return redirect("/")
    post_user_id = post_rows[0]["user_id"] if post_rows else None
    user_id = session.get("user_id")
    if post_user_id == user_id:
        posts.delete_post(post_id)
    else:
        flash("You are not authorized to delete this post", "error")
        return redirect(f"/post/{post_id}")
    return redirect("/")

@app.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    check_csrf()
    content = request.form["content"]
    user_id = session.get("user_id")
    content = content.strip()

    if not content:
        flash("Error: Comment content cannot be empty", "error")
        return redirect(f"/post/{post_id}")
    if len(content) > 160:
        flash("Error: Comment content cannot exceed 160 characters", "error")
        return redirect(f"/post/{post_id}")

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
        flash("Comment deleted successfully", "success")
        posts.delete_comment(comment_id)
    else:
        flash("You are not authorized to delete this comment", "error")
        return redirect(f"/post/{post_id}")
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
    return_to = request.form.get("return_to")
    if not return_to or not return_to.startswith("/") or return_to.startswith("//"):
        return_to = f"/post/{post_id}"
    return redirect(return_to)

# User Management

@app.route("/new_user")
def new_user():
    return render_template("new_user.html")

@app.route("/send_user", methods=["POST"])
def send_user():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    username = username.strip()

    if not username:
        flash("Username cannot be empty", "error")
        return redirect("/new_user")
    if not password1 or not password2:
        flash("Password cannot be empty", "error")
        return redirect("/new_user")
    if len(username) < 4 or len(username) > 16:
        flash("Username must be between 4 and 16 characters long", "error")
        return redirect("/new_user")
    if len(password1) < 8 or len(password1) > 20:
        flash("Password must be between 8 and 20 characters long", "error")
        return redirect("/new_user")
    if password1 != password2:
        flash("Passwords do not match", "error")
        return redirect("/new_user")

    hashed_password = generate_password_hash(password1)
    if not users.create_user(username, hashed_password):
        flash("Username already exists", "error")
        return redirect("/new_user")

    flash("User created successfully. Please log in.", "success")
    return redirect("/")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/send_login", methods=["POST"])
def send_login():
    username = request.form["username"]
    password = request.form["password"]

    if not username or not password:
        flash("Input your username and password", "error")
        return redirect("/login")

    user = users.get_user_by_username(username)

    if user and check_password_hash(user[0]["password_hash"], password):
        session["username"] = username
        session["user_id"] = user[0]["id"]
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")

    flash("Invalid username or password", "error")
    return redirect("/login")

@app.route("/logout", methods=["POST"])
def logout():
    check_csrf()
    del session["username"]
    del session["user_id"]
    return redirect("/login")

@app.route("/user/<username>")
def profile(username):
    user = users.get_user_by_username(username)
    if not user:
        flash("User not found", "error")
        return redirect("/")
    user_id = user[0]["id"]
    user_posts = posts.get_posts_by_user(user_id)
    total_posts = len(user_posts)
    total_likes = sum(posts.get_like_count(post["id"]) for post in user_posts)
    return render_template(
        "user.html",
        user=user[0], 
        posts=user_posts,
        total_posts=total_posts,
        total_likes=total_likes,
        username=session.get("username")
    )
