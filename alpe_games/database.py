"""
database.py
-----------
All SQLite database logic for the Alpe Games app.
Kept separate from app.py so the Streamlit UI code stays clean.
"""

import os
import sqlite3
from datetime import datetime

import pandas as pd

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "alpe_games.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ----------------------------------------------------------------------
# Connection helpers
# ----------------------------------------------------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they do not exist yet. Safe to call every run."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            image_path TEXT,
            author TEXT,
            event_date TEXT,
            created_at TEXT NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE,
            UNIQUE (event_id, session_id)
        )
        """
    )

    conn.commit()
    conn.close()


# ----------------------------------------------------------------------
# Event CRUD
# ----------------------------------------------------------------------
def add_event(title, description, image_path, author, event_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO events (title, description, image_path, author, event_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            description,
            image_path,
            author,
            str(event_date),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_event(event_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_events():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM events ORDER BY created_at DESC", conn)
    conn.close()
    return df


def update_event(event_id, title, description, author, event_date, image_path=None):
    conn = get_connection()
    cur = conn.cursor()
    if image_path:
        cur.execute(
            """
            UPDATE events
            SET title = ?, description = ?, author = ?, event_date = ?, image_path = ?
            WHERE id = ?
            """,
            (title, description, author, str(event_date), image_path, event_id),
        )
    else:
        cur.execute(
            """
            UPDATE events
            SET title = ?, description = ?, author = ?, event_date = ?
            WHERE id = ?
            """,
            (title, description, author, str(event_date), event_id),
        )
    conn.commit()
    conn.close()


def delete_event(event_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT image_path FROM events WHERE id = ?", (event_id,))
    row = cur.fetchone()
    if row and row["image_path"]:
        img_path = os.path.join(BASE_DIR, row["image_path"])
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except OSError:
                pass
    cur.execute("DELETE FROM votes WHERE event_id = ?", (event_id,))
    cur.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()


# ----------------------------------------------------------------------
# Voting
# ----------------------------------------------------------------------
def has_voted(event_id, session_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM votes WHERE event_id = ? AND session_id = ?",
        (event_id, session_id),
    )
    row = cur.fetchone()
    conn.close()
    return row is not None


def add_vote(event_id, session_id, rating):
    """Insert a vote. Returns False if this session already voted."""
    if has_voted(event_id, session_id):
        return False
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO votes (event_id, session_id, rating, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (event_id, session_id, rating, datetime.now().isoformat(timespec="seconds")),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return False
    conn.close()
    return True


def get_votes_for_event(event_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM votes WHERE event_id = ? ORDER BY created_at DESC", conn, params=(event_id,)
    )
    conn.close()
    return df


def get_all_votes():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM votes", conn)
    conn.close()
    return df


def reset_votes_for_event(event_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM votes WHERE event_id = ?", (event_id,))
    conn.commit()
    conn.close()


def reset_all_votes():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM votes")
    conn.commit()
    conn.close()


def reset_everything():
    """Wipe events, votes and uploaded images. Used by Admin > danger zone."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM votes")
    cur.execute("DELETE FROM events")
    conn.commit()
    conn.close()
    for f in os.listdir(UPLOAD_DIR):
        try:
            os.remove(os.path.join(UPLOAD_DIR, f))
        except OSError:
            pass


# ----------------------------------------------------------------------
# Leaderboard / analytics
# ----------------------------------------------------------------------
def get_leaderboard_df():
    """
    Returns a DataFrame with one row per event, including:
    average_rating, total_votes, position (1 = best).
    Events with zero votes are included at the bottom (average_rating = 0).
    Sorting: average_rating desc, then total_votes desc, then oldest first.
    """
    events = get_all_events()
    votes = get_all_votes()

    if events.empty:
        return pd.DataFrame(
            columns=[
                "id", "title", "description", "image_path", "author",
                "event_date", "created_at", "average_rating", "total_votes", "position",
            ]
        )

    if votes.empty:
        agg = pd.DataFrame(columns=["event_id", "average_rating", "total_votes"])
    else:
        agg = (
            votes.groupby("event_id")["rating"]
            .agg(average_rating="mean", total_votes="count")
            .reset_index()
        )

    merged = events.merge(agg, left_on="id", right_on="event_id", how="left")
    merged["average_rating"] = merged["average_rating"].fillna(0).round(2)
    merged["total_votes"] = merged["total_votes"].fillna(0).astype(int)

    merged = merged.sort_values(
        by=["average_rating", "total_votes", "created_at"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    merged["position"] = merged.index + 1
    merged = merged.drop(columns=["event_id"], errors="ignore")
    return merged


def get_stats_summary():
    events = get_all_events()
    votes = get_all_votes()
    total_events = len(events)
    total_votes = len(votes)
    avg_rating = round(votes["rating"].mean(), 2) if not votes.empty else 0.0
    return {
        "total_events": total_events,
        "total_votes": total_votes,
        "avg_rating": avg_rating,
    }
