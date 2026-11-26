import random
import sqlite3

db = sqlite3.connect("database.db")

db.execute("DELETE FROM posts")
db.execute("DELETE FROM users")
db.execute("DELETE FROM comments")
db.execute("DELETE FROM likes")

user_count = 1000
post_count = 10**5
comment_count = 10**6
likes_count = 10**6

file = open("test_picture.jpg", "rb")
picture = file.read()

topics = ["Nature", "Art", "Travel", "Food", "Sports", "Music", "Fashion", "Other"]

for i in range(1, user_count+1):
    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
               (f"user{i}", f"password{i}"))

for i in range(1, post_count+1):
    user_id = random.randint(1, user_count)
    topic = random.choice(topics)
    db.execute("INSERT INTO posts (title, content, topic, picture, user_id) VALUES (?, ?, ?, ?, ?)",
               (f"Post Title {i}", f"Post Content {i}", topic, picture, user_id))

for i in range(1, comment_count+1):
    user_id = random.randint(1, user_count)
    post_id = random.randint(1, post_count)
    db.execute("INSERT INTO comments (content, user_id, post_id) VALUES (?, ?, ?)",
               (f"Comment Content {i}", user_id, post_id))

db.commit()
db.close()