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