from flask import Flask, render_template, redirect, url_for
import db

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


sortstate_user = "Newest"

def sort_change_user(username):
    global sortstate_user
    if sortstate_user == "Newest":
        sortstate_user = "Oldest"
    elif sortstate_user == "Oldest":
        sortstate_user = "Most Liked"
    else:
        sortstate_user = "Newest"
    return redirect("/user/{}".format(username))
