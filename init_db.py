# -*- coding: utf-8 -*-
import sqlite3
import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).resolve().parent

DB_DIR = APP_DIR / "database"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "prompt_manager.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            is_starred INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );
        CREATE TABLE IF NOT EXISTS prompt_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            FOREIGN KEY (prompt_id) REFERENCES prompts(id)
        );
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            content TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prompt_id) REFERENCES prompts(id)
        );
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            combined_text TEXT,
            separator TEXT DEFAULT '\n\n',
            is_starred INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS collection_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_id INTEGER NOT NULL,
            prompt_id INTEGER NOT NULL,
            prompt_version_id INTEGER NOT NULL,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (collection_id) REFERENCES collections(id),
            FOREIGN KEY (prompt_id) REFERENCES prompts(id),
            FOREIGN KEY (prompt_version_id) REFERENCES prompt_versions(id)
        );
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user_id INTEGER NOT NULL,
            to_user_id INTEGER NOT NULL,
            shared_type TEXT NOT NULL,
            original_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user_id) REFERENCES users(id),
            FOREIGN KEY (to_user_id) REFERENCES users(id)
        );
    """)
    # 升級舊資料庫：加入新欄位（如果不存在）
    for col, definition in [
        ("sort_order", "INTEGER DEFAULT 0"),
        ("is_starred", "INTEGER DEFAULT 0"),
    ]:
        try:
            c.execute(f"ALTER TABLE prompts ADD COLUMN {col} {definition}")
        except Exception:
            pass
    for col, definition in [
        ("separator", "TEXT DEFAULT '\n\n'"),
        ("is_starred", "INTEGER DEFAULT 0"),
    ]:
        try:
            c.execute(f"ALTER TABLE collections ADD COLUMN {col} {definition}")
        except Exception:
            pass
    try:
        c.execute("CREATE TABLE IF NOT EXISTS prompt_tags (id INTEGER PRIMARY KEY AUTOINCREMENT, prompt_id INTEGER NOT NULL, tag TEXT NOT NULL, FOREIGN KEY (prompt_id) REFERENCES prompts(id))")
    except Exception:
        pass
    # 升級舊資料庫：加入新欄位
    for col, definition in [
        ("is_admin", "INTEGER DEFAULT 0"),
        ("status", "TEXT DEFAULT 'active'"),
    ]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
        except Exception:
            pass
    conn.commit()
    conn.close()
    print("DB ready:", DB_PATH)

if __name__ == "__main__":
    init_db()
