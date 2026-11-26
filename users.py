import sqlite3

import db


def create_user(username, password_hash):
    try:
        db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            [username, password_hash],
        )
    except sqlite3.IntegrityError:
        return False
    return True


def get_user_by_username(username):
    return db.query(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        [username],
    )

def get_username_by_id(user_id):
    return db.query("SELECT username FROM users WHERE id = ?", [user_id])
