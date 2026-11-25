import secrets

from flask import Flask, abort, redirect, request, session

import config
from .routes.auth import bp as auth_bp
from .routes.posts import bp as posts_bp

app = Flask(__name__)
app.secret_key = config.secret_key

@app.before_request
def before_request():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    csrf_token = session["csrf_token"]
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        submitted_token = request.form.get("csrf_token")
        if not submitted_token or not secrets.compare_digest(
            csrf_token.encode(), submitted_token.encode()
        ):
            abort(403)

    public_endpoints = {
        "auth.login",
        "auth.send_login",
        "auth.new_user",
        "auth.send_user",
    }
    if session.get("username") is None and request.endpoint not in public_endpoints:
        return redirect("/login")

app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
