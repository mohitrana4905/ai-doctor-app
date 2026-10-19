"""SQLite database layer for the AI Doctor Streamlit app."""
import sqlite3
import hashlib
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "aidoctor.db")


def _conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = _conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            age INTEGER,
            gender TEXT,
            blood_group TEXT,
            height_cm REAL,
            weight_kg REAL,
            allergies TEXT,
            conditions TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT,
            analysis TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vtype TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            taken_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            medicine TEXT NOT NULL,
            dosage TEXT,
            times TEXT,
            notes TEXT,
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    c.commit()
    c.close()


def _hash(password: str, salt: str = "aidoctor") -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()


def register_user(name, email, password):
    email = email.strip().lower()
    c = _conn()
    try:
        cur = c.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?,?,?,?)",
            (name.strip(), email, _hash(password), datetime.now().isoformat(timespec="seconds")),
        )
        uid = cur.lastrowid
        c.execute("INSERT INTO profiles (user_id) VALUES (?)", (uid,))
        c.commit()
        return uid, None
    except sqlite3.IntegrityError:
        return None, "An account with this email already exists. Try logging in."
    finally:
        c.close()


def login_user(email, password):
    email = email.strip().lower()
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    c.close()
    if row and row["password_hash"] == _hash(password):
        return dict(row), None
    return None, "Invalid email or password."


def get_profile(user_id):
    c = _conn()
    row = c.execute("SELECT * FROM profiles WHERE user_id=?", (user_id,)).fetchone()
    c.close()
    return dict(row) if row else {}


def save_profile(user_id, data: dict):
    c = _conn()
    c.execute(
        """UPDATE profiles SET age=?, gender=?, blood_group=?, height_cm=?, weight_kg=?,
           allergies=?, conditions=? WHERE user_id=?""",
        (data.get("age"), data.get("gender"), data.get("blood_group"),
         data.get("height_cm"), data.get("weight_kg"),
         data.get("allergies"), data.get("conditions"), user_id),
    )
    c.commit()
    c.close()


def save_chat(user_id, role, content):
    c = _conn()
    c.execute(
        "INSERT INTO chats (user_id, role, content, created_at) VALUES (?,?,?,?)",
        (user_id, role, content, datetime.now().isoformat(timespec="seconds")),
    )
    c.commit()
    c.close()


def get_chats(user_id, limit=60):
    c = _conn()
    rows = c.execute(
        "SELECT role, content FROM chats WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    c.close()
    return [dict(r) for r in reversed(rows)]


def clear_chats(user_id):
    c = _conn()
    c.execute("DELETE FROM chats WHERE user_id=?", (user_id,))
    c.commit()
    c.close()


def save_report(user_id, filename, analysis: dict):
    c = _conn()
    c.execute(
        "INSERT INTO reports (user_id, filename, analysis, created_at) VALUES (?,?,?,?)",
        (user_id, filename, json.dumps(analysis), datetime.now().isoformat(timespec="seconds")),
    )
    c.commit()
    c.close()


def get_reports(user_id):
    c = _conn()
    rows = c.execute(
        "SELECT id, filename, analysis, created_at FROM reports WHERE user_id=? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    c.close()
    out = []
    for r in rows:
        d = dict(r)
        d["analysis"] = json.loads(d["analysis"])
        out.append(d)
    return out


def add_vital(user_id, vtype, value, unit):
    c = _conn()
    c.execute(
        "INSERT INTO vitals (user_id, vtype, value, unit, taken_at) VALUES (?,?,?,?,?)",
        (user_id, vtype, value, unit, datetime.now().isoformat(timespec="seconds")),
    )
    c.commit()
    c.close()


def get_vitals(user_id, vtype=None):
    c = _conn()
    if vtype:
        rows = c.execute(
            "SELECT * FROM vitals WHERE user_id=? AND vtype=? ORDER BY id DESC LIMIT 50",
            (user_id, vtype),
        ).fetchall()
    else:
        rows = c.execute(
            "SELECT * FROM vitals WHERE user_id=? ORDER BY id DESC LIMIT 100", (user_id,)
        ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def add_reminder(user_id, medicine, dosage, times, notes):
    c = _conn()
    c.execute(
        "INSERT INTO reminders (user_id, medicine, dosage, times, notes, created_at) VALUES (?,?,?,?,?,?)",
        (user_id, medicine, dosage, times, notes, datetime.now().isoformat(timespec="seconds")),
    )
    c.commit()
    c.close()


def get_reminders(user_id):
    c = _conn()
    rows = c.execute(
        "SELECT * FROM reminders WHERE user_id=? AND active=1 ORDER BY id DESC", (user_id,)
    ).fetchall()
    c.close()
    return [dict(r) for r in rows]


def delete_reminder(rid, user_id):
    c = _conn()
    c.execute("UPDATE reminders SET active=0 WHERE id=? AND user_id=?", (rid, user_id))
    c.commit()
    c.close()
