from flask import Blueprint, Response, abort, redirect, render_template, request, session

from .. import db

bp = Blueprint("posts", __name__)


@bp.route("/")
def index():
    search_query = request.args.get("q", "").strip()
    sort_orders = {
        "newest": "posts.created_at DESC, posts.id DESC",
        "oldest": "posts.created_at ASC, posts.id ASC",
        "most_liked": "like_count DESC, posts.created_at DESC, posts.id DESC",
    }
    sort_by = request.args.get("sort", "newest")
    if sort_by not in sort_orders:
        sort_by = "newest"

    sql = """
        SELECT posts.id, posts.title, posts.content,
               posts.picture IS NOT NULL AS has_picture,
               (SELECT COUNT(*) FROM likes WHERE likes.post_id = posts.id) AS like_count
        FROM posts
    """
    params = []
    if search_query:
        sql += " WHERE posts.title LIKE ?"
        params.append(f"%{search_query}%")
    sql += f" ORDER BY {sort_orders[sort_by]}"
    posts = db.query(sql, params)
    return render_template(
        "index.html",
        posts=posts,
        username=session["username"],
        search_query=search_query,
        sort_by=sort_by,
    )


@bp.route("/new")
def new():
    return render_template("new.html")


@bp.route("/send", methods=["POST"])
def send():
    content = request.form["content"]
    title = request.form["title"]
    username = session.get("username")
    file = request.files.get("picture")
    if file is None or not file.filename:
        return "Error: No image uploaded", 400
    if not file.filename.lower().endswith(".jpg"):
        return "Error: Only JPG images are allowed", 400
    image = file.read()
    if len(image) > 100 * 1024:
        return "Error: Image size exceeds 100KB limit", 400

    db.execute(
        """
        INSERT INTO posts (title, content, user_id, picture)
        VALUES (?, ?, (SELECT id FROM users WHERE username = ?), ?)
        """,
        [title, content, username, image],
    )
    return redirect("/")


@bp.route("/post/<int:post_id>")
def post(post_id):
    post = db.query("SELECT id, title, content, user_id FROM posts WHERE id = ?", [post_id])
    comments = db.query(
        "SELECT comments.id, comments.post_id, comments.content, "
        "comments.user_id, users.username AS author "
        "FROM comments "
        "JOIN users ON comments.user_id = users.id "
        "WHERE comments.post_id = ?",
        [post_id],
    )
    likes = db.query("SELECT COUNT(*) as like_count FROM likes WHERE post_id = ?", [post_id])
    like_count = likes[0][0]
    author = db.query("SELECT username FROM users WHERE id = ?", [post[0]["user_id"]]) if post else None
    owner = session.get("user_id") == post[0]["user_id"] if post else False

    if post:
        return render_template(
            "post.html",
            post=post[0],
            comments=comments,
            likes=like_count,
            author=author[0]["username"],
            username=session.get("username"),
            owner=owner,
        )
    return "Post not found", 404


@bp.route("/post/<int:post_id>/picture")
def post_picture(post_id):
    rows = db.query("SELECT picture FROM posts WHERE id = ?", [post_id])
    if not rows or rows[0]["picture"] is None:
        abort(404)
    return Response(rows[0]["picture"], mimetype="image/jpeg")


@bp.route("/delete/<int:post_id>", methods=["POST"])
def delete(post_id):
    post = db.query("SELECT user_id FROM posts WHERE id = ?", [post_id])
    post_user_id = post[0]["user_id"] if post else None
    user_id = session.get("user_id")
    if post_user_id == user_id:
        db.execute("DELETE FROM posts WHERE id = ?", [post_id])
        db.execute("DELETE FROM comments WHERE post_id = ?", [post_id])
        db.execute("DELETE FROM likes WHERE post_id = ?", [post_id])
    else:
        return "You are not authorized to delete this post", 403
    return redirect("/")


@bp.route("/comment/<int:post_id>", methods=["POST"])
def comment(post_id):
    content = request.form["content"]
    user_id = session.get("user_id")
    db.execute(
        "INSERT INTO comments (post_id, content, user_id) VALUES (?, ?, ?)",
        [post_id, content, user_id],
    )
    return redirect(f"/post/{post_id}")


@bp.route("/delete_comment/<int:comment_id>", methods=["POST"])
def delete_comment(comment_id):
    comment = db.query("SELECT user_id, post_id FROM comments WHERE id = ?", [comment_id])
    comment_user_id = comment[0]["user_id"] if comment else None
    post_id = comment[0]["post_id"] if comment else None
    user_id = session.get("user_id")
    if comment_user_id == user_id:
        db.execute("DELETE FROM comments WHERE id = ?", [comment_id])
    else:
        return "You are not authorized to delete this comment", 403
    return redirect(f"/post/{post_id}")


@bp.route("/like/<int:post_id>", methods=["POST"])
def like(post_id):
    user_id = session.get("user_id")
    existing_like = db.query(
        "SELECT * FROM likes WHERE post_id = ? AND user_id = ?", [post_id, user_id]
    )
    if not existing_like:
        db.execute("INSERT INTO likes (post_id, user_id) VALUES (?, ?)", [post_id, user_id])
    if existing_like:
        db.execute("DELETE FROM likes WHERE post_id = ? AND user_id = ?", [post_id, user_id])
    return redirect(f"/post/{post_id}")