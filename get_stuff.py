
import db


def get_post(post_id):
    sql = "SELECT * FROM posts WHERE id = ?"
    post = db.query(sql, [post_id])
    return post[0] if post else None

def get_user(user_id):
    sql = "SELECT * FROM users WHERE id = ?"
    user = db.query(sql, [user_id])
    return user[0] if user else None