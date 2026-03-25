
import db


def get_post(post_id):
    sql = "SELECT * FROM posts WHERE id = ?"
    post = db.query(sql, [post_id])
    return post[0] if post else None

def get_user(user_id):
    sql = "SELECT * FROM users WHERE id = ?"
    user = db.query(sql, [user_id])
    return user[0] if user else None

def get_comments(post_id):
    sql = "SELECT * FROM comments WHERE post_id = ? ORDER BY created_at ASC"
    return db.query(sql, [post_id])

def get_comment(comment_id):
    sql = "SELECT * FROM comments WHERE id = ?"
    comment = db.query(sql, [comment_id])
    return comment[0] if comment else None