# -*- coding: utf-8 -*-
"""SQLite 数据层。

这个小软件自己维护一份数据库，与邮件推送版完全隔离：
邮件版的 state.json 只被**只读**地读取一次，绝不写回。

为什么必须自己建库：state.json 只存"当前在招"，岗位下架就被删掉，
而且记录里没有"首次出现日期"。历史和 post date 只能由本软件自己积累。
"""

import json
import sqlite3
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    key          TEXT PRIMARY KEY,
    source       TEXT NOT NULL,
    title        TEXT,
    link         TEXT,
    institution  TEXT,
    researchers  TEXT,
    fields       TEXT,
    deadline_raw TEXT,
    location     TEXT,
    start_date   TEXT,
    visa         TEXT,
    notes        TEXT,
    raw_meta     TEXT,
    tags         TEXT,            -- JSON 数组
    first_seen   TEXT NOT NULL,   -- 本软件首次抓到它的日期，即界面上的 post date
    last_seen    TEXT NOT NULL,   -- 最后一次出现在 state.json 里的日期
    status       TEXT NOT NULL DEFAULT 'open',   -- open | closed（已下架）
    is_initial   INTEGER NOT NULL DEFAULT 0,     -- 建库那天批量导入的存量岗位
    unread       INTEGER NOT NULL DEFAULT 0      -- 未读：只有真正的新增才置 1
);
CREATE INDEX IF NOT EXISTS idx_jobs_first_seen ON jobs(first_seen);
CREATE INDEX IF NOT EXISTS idx_jobs_status     ON jobs(status);

CREATE TABLE IF NOT EXISTS stars (
    key          TEXT PRIMARY KEY,
    starred_at   TEXT NOT NULL,
    remind_on    TEXT,            -- YYYY-MM-DD，可为空表示不提醒
    remind_basis TEXT,            -- deadline | rolling | manual
    note         TEXT,
    done         INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_stars_remind ON stars(remind_on);

CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init(conn):
    conn.executescript(SCHEMA)
    # 迁移：早期版本的库没有 unread 列
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(jobs)")}
    if "unread" not in cols:
        conn.execute("ALTER TABLE jobs ADD COLUMN unread INTEGER NOT NULL DEFAULT 0")
    conn.commit()


def get_meta(conn, k, default=None):
    row = conn.execute("SELECT v FROM meta WHERE k = ?", (k,)).fetchone()
    return row["v"] if row else default


def set_meta(conn, k, v):
    conn.execute(
        "INSERT INTO meta(k, v) VALUES(?, ?) ON CONFLICT(k) DO UPDATE SET v = excluded.v",
        (k, str(v)),
    )


def is_initialized(conn):
    return get_meta(conn, "initialized_on") is not None


# ---------------------------------------------------------------- 查询

SOURCE_LABELS = {
    "predoc": "predoc.org",
    "nber": "NBER（本部）",
    "nber_external": "NBER（非本部）",
}


def _rows(cur):
    out = []
    for r in cur.fetchall():
        d = dict(r)
        try:
            d["tags"] = json.loads(d.get("tags") or "[]")
        except (ValueError, TypeError):
            d["tags"] = []
        d["source_label"] = SOURCE_LABELS.get(d.get("source"), d.get("source"))
        out.append(d)
    return out


def search_jobs(conn, q="", source="", status="", starred_only=False,
                order="first_seen", limit=500, offset=0):
    """关键词跨 领域 / 导师 / 机构 / 标题 检索。

    208 条数据量下 LIKE 完全够用，不需要 FTS。空格分隔的多个词按 AND 处理，
    这样 "labor harvard" 能同时命中领域和机构。
    """
    sql = ["SELECT j.*, s.key IS NOT NULL AS starred, s.remind_on, s.done",
           "FROM jobs j LEFT JOIN stars s ON s.key = j.key WHERE 1=1"]
    args = []
    for term in [t for t in (q or "").split() if t]:
        sql.append("""AND (j.title LIKE ? OR j.fields LIKE ? OR j.researchers LIKE ?
                          OR j.institution LIKE ? OR j.tags LIKE ? OR j.raw_meta LIKE ?)""")
        args.extend(["%%%s%%" % term] * 6)
    if source:
        sql.append("AND j.source = ?")
        args.append(source)
    if status:
        sql.append("AND j.status = ?")
        args.append(status)
    if starred_only:
        sql.append("AND s.key IS NOT NULL")
    orders = {
        "first_seen": "j.first_seen DESC, j.title ASC",
        "title": "j.title ASC",
        "institution": "j.institution ASC, j.title ASC",
        "remind": "s.remind_on IS NULL, s.remind_on ASC",
    }
    sql.append("ORDER BY " + orders.get(order, orders["first_seen"]))
    sql.append("LIMIT ? OFFSET ?")
    args.extend([limit, offset])
    return _rows(conn.execute(" ".join(sql), args))


def count_jobs(conn, **kw):
    kw.pop("limit", None)
    kw.pop("offset", None)
    return len(search_jobs(conn, limit=100000, **kw))


def get_job(conn, key):
    rows = _rows(conn.execute(
        "SELECT j.*, s.key IS NOT NULL AS starred, s.remind_on, s.remind_basis, s.note, s.done "
        "FROM jobs j LEFT JOIN stars s ON s.key = j.key WHERE j.key = ?", (key,)))
    return rows[0] if rows else None


def unread_jobs(conn):
    """尚未被标记为已读的新增岗位。

    用一个显式的 unread 标记，而不是"上次打开时间"之类的日期水位：
    日期水位在"同一天里先标已读、之后又抓到新岗位"时会把那批岗位永久跳过。
    标记法没有这个问题，刷新页面也不会把未读列表刷没 —— 只有用户主动
    点"标记已读"才清零。
    """
    return _rows(conn.execute(
        "SELECT j.*, s.key IS NOT NULL AS starred, s.remind_on FROM jobs j "
        "LEFT JOIN stars s ON s.key = j.key "
        "WHERE j.unread = 1 ORDER BY j.first_seen DESC, j.source, j.title"))


def mark_all_read(conn):
    n = conn.execute("UPDATE jobs SET unread = 0 WHERE unread = 1").rowcount
    conn.commit()
    return n


def starred_jobs(conn, include_done=True):
    sql = ("SELECT j.*, 1 AS starred, s.starred_at, s.remind_on, s.remind_basis, s.note, s.done "
           "FROM stars s JOIN jobs j ON j.key = s.key ")
    if not include_done:
        sql += "WHERE s.done = 0 "
    sql += "ORDER BY s.done ASC, s.remind_on IS NULL, s.remind_on ASC"
    return _rows(conn.execute(sql))


def reminders_between(conn, start, end):
    return _rows(conn.execute(
        "SELECT j.*, 1 AS starred, s.remind_on, s.remind_basis, s.note, s.done "
        "FROM stars s JOIN jobs j ON j.key = s.key "
        "WHERE s.remind_on IS NOT NULL AND s.remind_on >= ? AND s.remind_on <= ? "
        "ORDER BY s.remind_on ASC", (start, end)))


# ---------------------------------------------------------------- 写入

def star(conn, key, remind_on, basis, note=""):
    conn.execute(
        "INSERT INTO stars(key, starred_at, remind_on, remind_basis, note) VALUES(?,?,?,?,?) "
        "ON CONFLICT(key) DO UPDATE SET remind_on=excluded.remind_on, "
        "remind_basis=excluded.remind_basis, note=excluded.note",
        (key, date.today().isoformat(), remind_on or None, basis, note or ""))
    conn.commit()


def unstar(conn, key):
    conn.execute("DELETE FROM stars WHERE key = ?", (key,))
    conn.commit()


def set_done(conn, key, done):
    conn.execute("UPDATE stars SET done = ? WHERE key = ?", (1 if done else 0, key))
    conn.commit()


def stats(conn):
    row = conn.execute(
        "SELECT COUNT(*) n, SUM(status='open') opened, SUM(status='closed') closed FROM jobs"
    ).fetchone()
    starred = conn.execute("SELECT COUNT(*) n FROM stars").fetchone()["n"]
    per_source = {r["source"]: r["n"] for r in conn.execute(
        "SELECT source, COUNT(*) n FROM jobs WHERE status='open' GROUP BY source")}
    return {"total": row["n"] or 0, "open": row["opened"] or 0,
            "closed": row["closed"] or 0, "starred": starred, "per_source": per_source}
