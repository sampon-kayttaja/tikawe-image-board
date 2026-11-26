import db


def get_posts(search_query, sort_by):
    sort_orders = {
        "newest": "posts.created_at DESC, posts.id DESC",
        "oldest": "posts.created_at ASC, posts.id ASC",
        "most_liked": "like_count DESC, posts.created_at DESC, posts.id DESC",
    }
    if sort_by not in sort_orders:
        sort_by = "newest"

    sql = """
        SELECT posts.id, posts.title, posts.content, posts.topic,
               users.username,
               posts.picture IS NOT NULL AS has_picture,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
        FROM posts
        LEFT JOIN users ON posts.user_id = users.id
    """
    params = []
    if search_query:
        sql += " WHERE posts.title LIKE ?"
        params.append(f"%{search_query}%")
    sql += f" ORDER BY {sort_orders[sort_by]}"
    return db.query(sql, params)


def create_post(title, content, topic, username, image):
    db.execute(
        """
        INSERT INTO posts (title, content, topic, user_id, picture)
        VALUES (?, ?, ?, (SELECT id FROM users WHERE username = ?), ?)
        """,
        [title, content, topic, username, image],
    )


def get_post(post_id):
    return db.query(
        "SELECT id, title, content, topic, user_id, created_at FROM posts WHERE id = ?", [post_id]
    )


def get_comments(post_id):
    return db.query(
        "SELECT comments.id, comments.post_id, comments.content, "
        "comments.user_id, users.username AS author "
        "FROM comments "
        "JOIN users ON comments.user_id = users.id "
        "WHERE comments.post_id = ?",
        [post_id],
    )


def get_like_count(post_id):
    rows = db.query(
        "SELECT COUNT(*) as like_count FROM likes WHERE post_id = ?", [post_id]
    )
    return rows[0][0]


def get_picture(post_id):
    return db.query("SELECT picture FROM posts WHERE id = ?", [post_id])


def get_post_user_id(post_id):
    return db.query("SELECT user_id FROM posts WHERE id = ?", [post_id])


def delete_post(post_id):
    db.execute("DELETE FROM posts WHERE id = ?", [post_id])
    db.execute("DELETE FROM comments WHERE post_id = ?", [post_id])
    db.execute("DELETE FROM likes WHERE post_id = ?", [post_id])


def create_comment(post_id, content, user_id):
    db.execute(
        "INSERT INTO comments (post_id, content, user_id) VALUES (?, ?, ?)",
        [post_id, content, user_id],
    )


def get_comment(comment_id):
    return db.query(
        "SELECT user_id, post_id FROM comments WHERE id = ?", [comment_id]
    )


def delete_comment(comment_id):
    db.execute("DELETE FROM comments WHERE id = ?", [comment_id])


def get_like(post_id, user_id):
    return db.query(
        "SELECT * FROM likes WHERE post_id = ? AND user_id = ?", [post_id, user_id]
    )


def add_like(post_id, user_id):
    db.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", [post_id, user_id])


def remove_like(post_id, user_id):
    db.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", [post_id, user_id])


def update_post(post_id, title, content, topic):
    db.execute(
        "UPDATE posts SET title = ?, content = ?, topic = ? WHERE id = ?",
        [title, content, topic, post_id],
    )

def get_posts_by_user(user_id):
    return db.query(
        "SELECT posts.id, posts.title, posts.content, posts.topic, posts.created_at, "
        "(SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count "
        "FROM posts "
        "WHERE posts.user_id = ? "
        "ORDER BY posts.created_at DESC",
        [user_id],
    )
