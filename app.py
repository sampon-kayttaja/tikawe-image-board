import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import config
import db

app = Flask(__name__)
app.secret_key = config.secret_key

upload_folder = 'static/uploads/'
allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route("/")
def index():
    posts = db.query("SELECT * FROM posts ORDER BY created_at DESC LIMIT 10")   # Fetch latest 10 posts from database. No database yet implemented.
                                                                                # Database will have id, username, title, image_url, content, created_at fields in this order.
                                                                                # Each post will display title, image (if image_url is not empty), content, username, created_at
                                                                                # Each post will have a link to view comments (not implemented yet)
                                                                                # Comment section will be its own datapage (not implemented yet)
    
    return render_template("index.html", posts=posts)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    # Common error timer for all errors

    error_timer = "<script>setTimeout(function(){ window.location.href = '/register'; }, 2000);</script>"

    # Username validation

    if username == "" or password1 == "" or password2 == "":
        return "ERROR: All fields are required!" + error_timer

    if len(username) < 4 or len(username) > 20:
        return "ERROR: Username must be between 4 and 20 characters!" + error_timer

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
        return "ERROR: Password must be at least 6 characters long and include both letters and numbers." + error_timer
        
    if password1 != password2:
        return "ERROR: Passwords do not match." + error_timer

    password_hash = generate_password_hash(password1)

    # Insert new user into database

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
        return redirect("/")
    else:
        return errormsg

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/new_post", methods=["POST", "GET"])
def new_post():
    return render_template("new_post.html")

@app.route("/create_post", methods=["POST"])
def create_post():
    if "username" not in session:
        return "You must be logged in to create a post." + "<script>setTimeout(function(){ window.location.href = '/'; }, 2000);</script>"
    title = request.form.get("title", "").strip()
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
            return "File type not allowed" + "<script>setTimeout(function(){ window.location.href = '/new_post'; }, 2000);</script>"

    sql = "INSERT INTO posts (username, title, image_url, content, created_at) VALUES (?, ?, ?, ?, datetime('now'))"
    db.execute(sql, [username, title, image_url, content])
    return redirect("/")

