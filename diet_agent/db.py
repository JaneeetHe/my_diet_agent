"""SQLite 存档：每条记录一行。"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path

from .foods import ROOT

DB_PATH = Path(os.environ.get("DIET_DB", ROOT / "data" / "diet.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT NOT NULL,
    meal       TEXT NOT NULL DEFAULT '',
    code       TEXT,
    name       TEXT NOT NULL,
    qty        REAL NOT NULL,
    kcal       REAL NOT NULL,
    protein    REAL NOT NULL,
    carb       REAL NOT NULL,
    fat        REAL NOT NULL,
    source     TEXT NOT NULL,
    raw        TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(date);
CREATE TABLE IF NOT EXISTS notes (
    date TEXT PRIMARY KEY,
    note TEXT
);
"""


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # MCP 框架在工作线程里执行工具，连接需允许跨线程使用
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def add_items(conn, date: str, meal: str, items) -> list[int]:
    now = datetime.now().isoformat(timespec="seconds")
    ids = []
    with conn:
        for it in items:
            cur = conn.execute(
                "INSERT INTO entries(date, meal, code, name, qty, kcal, protein, carb, fat, source, raw, created_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (date, meal, it.code, it.name, it.qty, it.kcal, it.protein,
                 it.carb, it.fat, it.source, it.raw, now))
            ids.append(cur.lastrowid)
    return ids


def day_rows(conn, date: str) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM entries WHERE date=? ORDER BY id", (date,)).fetchall()


def delete(conn, entry_id: int) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM entries WHERE id=?", (entry_id,)).fetchone()
    if row:
        with conn:
            conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
    return row


def range_totals(conn, start: str, end: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT date, SUM(kcal) kcal, SUM(protein) protein, SUM(carb) carb, SUM(fat) fat"
        " FROM entries WHERE date BETWEEN ? AND ? GROUP BY date ORDER BY date",
        (start, end)).fetchall()


def set_note(conn, date: str, note: str) -> None:
    with conn:
        conn.execute("INSERT INTO notes(date, note) VALUES(?,?) ON CONFLICT(date) DO UPDATE SET note=excluded.note",
                     (date, note))


def get_note(conn, date: str) -> str:
    row = conn.execute("SELECT note FROM notes WHERE date=?", (date,)).fetchone()
    return row["note"] if row else ""
