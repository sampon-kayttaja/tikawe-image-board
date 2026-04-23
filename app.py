import secrets
import sqlite3
import os
from flask import Flask, abort, jsonify, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import db
import get_stuff

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

upload_folder = 'static/uploads/'
allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

db.init_db()

#security

def check_csrf():
    if request.form["csrf_token"] != session.get("csrf_token"):
        abort(403)

#frontpage

@app.route("/")
def index():
    posts_by_new = db.query("SELECT id, username, title, image_url, content, created_at, likes FROM posts ORDER BY created_at DESC LIMIT 10")
    posts_by_old = db.query("SELECT id, username, title, image_url, content, created_at, likes FROM posts LIMIT 10")
    posts_by_likes = db.query("SELECT id, username, title, image_url, content, created_at, likes FROM posts ORDER BY likes DESC LIMIT 10")
    return render_template("index.html", posts_by_new=posts_by_new, posts_by_old=posts_by_old, posts_by_likes=posts_by_likes, sortstate=sortstate)

#sort posts by time or likes

sortstate = "Newest"

@app.route("/change_sort", methods=["GET"])
def sort_change():
    global sortstate
    if sortstate == "Newest":
        sortstate = "Oldest"
    elif sortstate == "Oldest":
        sortstate = "Most Liked"
    else:
        sortstate = "Newest"
    return redirect("/")

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

#post creation with optional image upload

@app.route("/new_post", methods=["POST", "GET"])
def new_post():
    return render_template("new_post.html")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route("/create_post", methods=["POST"])
def create_post():
    check_csrf()

    if "username" not in session:
        return "You must be logged in to create a post."
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    username = session["username"]

    #handle uploaded image if present
    image_url = ""
    file = request.files.get('image')
    if file and file.filename != "":
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = app.config.get('UPLOAD_FOLDER')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            #store a web-accessible path
            image_url = f"/static/uploads/{filename}"
        else:
            return "File type not allowed"

    sql = "INSERT INTO posts (username, title, image_url, content, created_at, likes) VALUES (?, ?, ?, ?, datetime('now'), ?)"
    db.execute(sql, [username, title, image_url, content, 0])
    return redirect("/")

#viewing and commenting on posts

@app.route("/post/<int:post_id>")
def view_post(post_id):
    post = get_stuff.get_post(post_id)
    if not post:
        return "Post not found."
    comments = db.query("SELECT id, post_id, username, content, image_url, created_at, likes FROM comments WHERE post_id = ? ORDER BY created_at ASC", [post_id])
    return render_template("view_post.html", post=post, comments=comments)

@app.route("/create_comment/<int:post_id>", methods=["POST"])
def create_comment(post_id):
    check_csrf()

    content = request.form.get("content", "").strip()
    username = session["username"]  

    # Handle uploaded image if present
    image_url = ""
    file = request.files.get('image')
    if file and file.filename != "":
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = app.config.get('UPLOAD_FOLDER')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            # Store a web-accessible path
            image_url = f"/static/uploads/{filename}"
        else:
            return "File type not allowed"

    sql = "INSERT INTO comments (post_id, username, content, image_url, created_at, likes) VALUES (?, ?, ?, ?, datetime('now'), ?)"
    db.execute(sql, [post_id, username, content, image_url, 0])
    return redirect("/post/{}".format(post_id))

#delete post and comment

@app.route("/delete_post/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    check_csrf()

    post = get_stuff.get_post(post_id)
    db.execute("DELETE FROM posts WHERE id = ?", [post_id])
    db.execute("DELETE FROM comments WHERE post_id = ?", [post_id])
    return redirect("/")
    
@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id): 
    check_csrf()

    comment = get_stuff.get_comment(comment_id)
    db.execute("DELETE FROM comments WHERE id = ?", [comment_id])
    return redirect("/post/{}".format(comment[1])) 

#edit posts and comments

@app.route("/edit_post/<int:post_id>")
def edit_post(post_id):
    post = get_stuff.get_post(post_id)
    return render_template("edit_post.html", post=post)

@app.route("/update_post/<int:post_id>", methods=["POST"])
def update_post(post_id, image_url=""):
    check_csrf()

    #handle uploaded image if present
    image_url = ""
    file = request.files.get('image')
    if file and file.filename != "":
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = app.config.get('UPLOAD_FOLDER')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            #store a web-accessible path
            image_url = f"/static/uploads/{filename}"
        else:
            return "File type not allowed"

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    db.execute("UPDATE posts SET title = ?, content = ?, image_url = ? WHERE id = ?", [title, content, image_url, post_id])
    return redirect("/post/{}".format(post_id))

@app.route("/edit_comment/<int:comment_id>")
def edit_comment(comment_id):
    comment = get_stuff.get_comment(comment_id)
    return render_template("edit_comment.html", comment=comment)

@app.route("/update_comment/<int:comment_id>", methods=["POST"])
def update_comment(comment_id, image_url=""):
    check_csrf()

    #handle uploaded image if present
    image_url = ""
    file = request.files.get('image')
    if file and file.filename != "":
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = app.config.get('UPLOAD_FOLDER')
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            #store a web-accessible path
            image_url = f"/static/uploads/{filename}"
        else:
            return "File type not allowed"

    content = request.form.get("content", "").strip()
    db.execute("UPDATE comments SET content = ?, image_url = ? WHERE id = ?", [content, image_url, comment_id])
    comment = get_stuff.get_comment(comment_id)
    return redirect("/post/{}".format(comment[1]))

#liking posts and comments

@app.route("/like_post/<int:post_id>", methods=["GET"])
def like_post(post_id):
    if "username" not in session:
        return "You must be logged in to like a post."  
    
    already_liked_post = db.query("SELECT COUNT(*) FROM post_likes WHERE post_id = ? AND username = ?", [post_id, session["username"]])[0][0] > 0
    post_id = db.query("SELECT id FROM posts WHERE id = ?", [post_id])[0][0]

    if already_liked_post:
        return render_template("already_liked.html", post_id=post_id)
    else:
        db.execute("INSERT INTO post_likes (post_id, username) VALUES (?, ?)", [post_id, session["username"]])
        db.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", [post_id])
    return redirect("/post/{}".format(post_id))

@app.route("/like_comment/<int:comment_id>", methods=["GET"])

def like_comment(comment_id):
    if "username" not in session:
        return "You must be logged in to like a comment."

    already_liked_comment = db.query("SELECT COUNT(*) FROM comment_likes WHERE comment_id = ? AND username = ?", [comment_id, session["username"]])[0][0] > 0
    post_id = db.query("SELECT post_id FROM comments WHERE id = ?", [comment_id])[0][0]

    if already_liked_comment:
        return render_template("already_liked_c.html", post_id=post_id)
    else:
        db.execute("UPDATE comments SET likes = likes + 1 WHERE id = ?", [comment_id])
        db.execute("INSERT INTO comment_likes (comment_id, username) VALUES (?, ?)", [comment_id, session["username"]])
    comment = get_stuff.get_comment(comment_id)
    return redirect("/post/{}".format(comment[1]))

#viewing users

sortstate_user = "Newest"

@app.route("/user/<username>")
def user_profile(username):
    user_posts_by_new = db.query("SELECT id, username, title, image_url, content, created_at, likes FROM posts WHERE username = ? ORDER BY created_at DESC", [username])
    user_posts_by_old = db.query("SELECT id, username, title, image_url, content, created_at, likes FROM posts WHERE username = ?", [username])
    user_posts_by_likes = db.query("SELECT id, username, title, image_url, content, created_at, likes FROM posts WHERE username = ? ORDER BY likes DESC", [username])
    likes_posts = user_posts_by_new[0]["likes"] if user_posts_by_new else 0
    user_comments = db.query("SELECT id, post_id, username, content, image_url, created_at, likes FROM comments WHERE username = ?", [username])
    likes_comments = user_comments[0]["likes"] if user_comments else 0
    likes = likes_posts + likes_comments
    comments = len(user_comments)

    return render_template("view_user.html", username=username, posts_by_new=user_posts_by_new, posts_by_old=user_posts_by_old, posts_by_likes=user_posts_by_likes, likes=likes, comments=comments, sortstate=sortstate_user)

@app.route("/change_sort_user/<username>", methods=["GET"])
def sort_change_user(username):
    global sortstate_user
    if sortstate_user == "Newest":
        sortstate_user = "Oldest"
    elif sortstate_user == "Oldest":
        sortstate_user = "Most Liked"
    else:
        sortstate_user = "Newest"
    return redirect("/user/{}".format(username))

#searching posts

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/search_results", methods=["GET"])
def search_results():
    query = request.args.get("query", "").strip()
    if query == "":
        return redirect("/search")    

    search_results = db.query("SELECT id, username, title, image_url, content, created_at, likes FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC", ['%' + query + '%', '%' + query + '%'])
    return render_template("search_results.html", query=query, results=search_results, count=len(search_results))




