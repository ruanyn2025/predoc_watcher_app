# -*- coding: utf-8 -*-
"""把邮件版的 state.json 导入本软件的数据库。

只读取，绝不写回 —— 邮件推送版的运行完全不受影响。

首次导入时全部岗位标记 is_initial=1，这样它们不会在首页被当成"新增"刷屏；
之后每次导入，state.json 里新出现的 key 才算真正的新增，并记录 first_seen
（就是界面上显示的 post date）。从 state.json 里消失的岗位不删除，
标记为 closed 留在历史里 —— 这正是邮件版做不到的事。
"""

import json
from datetime import date
from pathlib import Path

import db

BASE_DIR = Path(__file__).resolve().parent

# 邮件版被挪进 mailer/ 之后的位置；老布局（同级）作为退路，两种都能跑。
STATE_CANDIDATES = [
    BASE_DIR.parent / "mailer" / "state.json",
    BASE_DIR.parent / "state.json",
]

FIELD_MAP = ["title", "link", "institution", "researchers", "fields",
             "location", "start_date", "visa", "notes", "raw_meta"]


def find_state():
    for p in STATE_CANDIDATES:
        if p.is_file():
            return p
    return None


def load_state(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sources = data.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("state.json 结构不认识：缺少 sources")
    return sources


def ingest(conn, today=None, verbose=False):
    """返回 dict(added, updated, closed, reopened, total, initial)。"""
    today = (today or date.today()).isoformat()
    path = find_state()
    if path is None:
        raise FileNotFoundError(
            "找不到邮件版的 state.json，找过：\n  " +
            "\n  ".join(str(p) for p in STATE_CANDIDATES))

    sources = load_state(path)
    first_time = not db.is_initialized(conn)

    seen = set()
    added = updated = reopened = 0

    for source, items in sources.items():
        if not isinstance(items, dict):
            continue
        for key, rec in items.items():
            seen.add(key)
            row = conn.execute("SELECT key, status FROM jobs WHERE key = ?", (key,)).fetchone()
            values = {f: (rec.get(f) or "") for f in FIELD_MAP}
            values["deadline_raw"] = rec.get("deadline") or ""
            values["tags"] = json.dumps(rec.get("tags") or [], ensure_ascii=False)

            if row is None:
                conn.execute(
                    "INSERT INTO jobs(key, source, %s, deadline_raw, tags, first_seen, "
                    "last_seen, status, is_initial, unread) VALUES(?,?,%s,?,?,?,?,'open',?,?)"
                    % (",".join(FIELD_MAP), ",".join("?" * len(FIELD_MAP))),
                    [key, source] + [values[f] for f in FIELD_MAP] +
                    [values["deadline_raw"], values["tags"], today, today,
                     1 if first_time else 0,        # is_initial
                     0 if first_time else 1])       # unread：建库存量不算未读
                added += 1
            else:
                # 站方偶尔会就地改文案，这里同步过来，但绝不动 first_seen。
                conn.execute(
                    "UPDATE jobs SET %s, deadline_raw=?, tags=?, last_seen=?, status='open' "
                    "WHERE key=?" % ",".join("%s=?" % f for f in FIELD_MAP),
                    [values[f] for f in FIELD_MAP] +
                    [values["deadline_raw"], values["tags"], today, key])
                if row["status"] == "closed":
                    reopened += 1
                else:
                    updated += 1

    # 这次没出现的，视为已下架 —— 保留记录，只改状态。
    closed = 0
    for row in conn.execute("SELECT key FROM jobs WHERE status='open'").fetchall():
        if row["key"] not in seen:
            conn.execute("UPDATE jobs SET status='closed' WHERE key=?", (row["key"],))
            closed += 1

    if first_time:
        db.set_meta(conn, "initialized_on", today)
    db.set_meta(conn, "last_ingest_at", today)
    db.set_meta(conn, "state_path", str(path))
    conn.commit()

    result = {"added": added, "updated": updated, "closed": closed,
              "reopened": reopened, "total": len(seen), "initial": first_time,
              "path": str(path)}
    if verbose:
        print("导入自 %s" % path)
        print("  本次 state.json 共 %d 条" % result["total"])
        print("  新增 %d · 更新 %d · 下架 %d · 重新上架 %d%s"
              % (added, updated, closed, reopened,
                 "（首次建库，全部记为存量）" if first_time else ""))
    return result


if __name__ == "__main__":
    conn = db.connect()
    db.init(conn)
    ingest(conn, verbose=True)
    s = db.stats(conn)
    print("  库内合计 %d 条（在招 %d / 已下架 %d），收藏 %d"
          % (s["total"], s["open"], s["closed"], s["starred"]))
