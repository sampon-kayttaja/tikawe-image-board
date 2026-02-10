
CREATE table users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);


CREATE table posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    title TEXT,
    image_url TEXT,
    content TEXT,
    created_at DATETIME,
    likes INTEGER 
);

CREATE table comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    username TEXT,
    content TEXT,
    image_url TEXT,
    created_at DATETIME,
    likes INTEGER
);  