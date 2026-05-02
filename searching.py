import get_stuff
from flask import Flask, render_template, request, redirect
import db

def search_results():
    query = request.args.get("query", "").strip()
    if query == "":
        return redirect("/search_posts")    

    search_results = db.query("SELECT id, username, title, image_url, content, created_at, likes FROM posts WHERE title LIKE ? OR content LIKE ? ORDER BY created_at DESC", ['%' + query + '%', '%' + query + '%'])
    return render_template("search_posts_results.html", query=query, results=search_results, count=len(search_results))

def search_users_results():
    query = request.args.get("query", "").strip()
    if query == "":
        return redirect("/search_users")    

    search_results = db.query("SELECT username FROM users WHERE username LIKE ? ORDER BY username", ['%' + query + '%'])
    return render_template("search_users_results.html", query=query, results=search_results, count=len(search_results))