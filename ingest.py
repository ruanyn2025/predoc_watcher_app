# -*- coding: utf-8 -*-
"""把抓到的岗位写进本软件的数据库。

本软件自带抓取（见 fetch.py），**不依赖邮件推送版**。邮件版可以随时停用或删除。

`import_state_json()` 只是一次性的迁移入口：把邮件版历史留下的 state.json 当作
初始快照导入，让切换过来时不会把存量岗位全当成"新增"。日常运行不会用到它。
"""

import json
from datetime import date
from pathlib import Path

import db
import fetch

BASE_DIR = Path(__file__).resolve().parent

# 一次性迁移用：邮件版 state.json 的可能位置
STATE_CANDIDATES = [
    BASE_DIR.parent / "mailer" / "state.json",
    BASE_DIR.parent / "state.json",
]

FIELD_MAP = ["title", "link", "institution", "researchers", "fields",
             "location", "start_date", "visa", "notes", "raw_meta"]


def _upsert(conn, source, key, rec, today, first_time):
    """写入或更新一条岗位。first_seen 一旦定下就永不改动 —— 那是界面上的 post date。"""
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
             1 if first_time else 0,      # is_initial：建库存量
             0 if first_time else 1])     # unread：只有真正的新增才算未读
        return "added"

    # 站方偶尔就地改文案，同步过来，但绝不动 first_seen。
    conn.execute(
        "UPDATE jobs SET %s, deadline_raw=?, tags=?, last_seen=?, status='open' WHERE key=?"
        % ",".join("%s=?" % f for f in FIELD_MAP),
        [values[f] for f in FIELD_MAP] +
        [values["deadline_raw"], values["tags"], today, key])
    return "reopened" if row["status"] == "closed" else "updated"


def refresh(conn, source_ids=None, today=None, verbose=False):
    """抓取三个来源并写库。返回统计与各来源的成败。

    关键护栏：**抓取失败的来源，其岗位不会被标记为已下架**。否则站点临时故障
    会把整站岗位标成下架，等恢复了又全部变成"新增"轰炸一遍。
    """
    today = (today or date.today()).isoformat()
    first_time = not db.is_initialized(conn)

    results = fetch.collect_all(source_ids)
    counts = {"added": 0, "updated": 0, "reopened": 0, "closed": 0}
    seen_by_source = {}
    failures = {}

    for sid, r in results.items():
        if not r["ok"]:
            failures[sid] = r["error"]
            continue
        seen = set()
        for item in r["items"]:
            key = fetch.item_key(sid, item)
            seen.add(key)
            counts[_upsert(conn, sid, key, item, today, first_time)] += 1
        seen_by_source[sid] = seen

    # 只在抓取成功的来源内部判断下架；失败的来源原样保留。
    for sid, seen in seen_by_source.items():
        for row in conn.execute(
                "SELECT key FROM jobs WHERE source=? AND status='open'", (sid,)).fetchall():
            if row["key"] not in seen:
                conn.execute("UPDATE jobs SET status='closed' WHERE key=?", (row["key"],))
                counts["closed"] += 1

    if first_time:
        db.set_meta(conn, "initialized_on", today)
    db.set_meta(conn, "last_fetch_at", today)
    conn.commit()

    total = sum(len(s) for s in seen_by_source.values())
    result = dict(counts, total=total, initial=first_time, failures=failures,
                  ok_sources=list(seen_by_source))
    if verbose:
        for sid, r in results.items():
            name = fetch.SOURCE_BY_ID[sid]["name"]
            print("  [%s] %s" % (name, "%d 条" % len(r["items"]) if r["ok"]
                                 else "失败：" + r["error"]))
        print("  新增 %d · 更新 %d · 下架 %d · 重新上架 %d%s"
              % (counts["added"], counts["updated"], counts["closed"], counts["reopened"],
                 "（首次建库，全部记为存量）" if first_time else ""))
    return result


# ------------------------------------------------------- 一次性迁移

def find_state():
    for p in STATE_CANDIDATES:
        if p.is_file():
            return p
    return None


def import_state_json(conn, path=None, today=None, verbose=False):
    """把邮件版的 state.json 当初始快照导入。只在迁移时用一次。"""
    today = (today or date.today()).isoformat()
    path = Path(path) if path else find_state()
    if path is None or not path.is_file():
        raise FileNotFoundError("找不到 state.json，找过：\n  " +
                                "\n  ".join(str(p) for p in STATE_CANDIDATES))
    with open(path, encoding="utf-8") as f:
        sources = json.load(f).get("sources") or {}

    first_time = not db.is_initialized(conn)
    counts = {"added": 0, "updated": 0, "reopened": 0}
    for source, items in sources.items():
        if not isinstance(items, dict):
            continue
        for key, rec in items.items():
            counts[_upsert(conn, source, key, rec, today, first_time)] += 1
    if first_time:
        db.set_meta(conn, "initialized_on", today)
    conn.commit()
    if verbose:
        print("自 %s 导入：新增 %d · 更新 %d" % (path, counts["added"], counts["updated"]))
    return counts


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="抓取岗位并写库")
    ap.add_argument("--from-state", metavar="PATH", nargs="?", const="",
                    help="一次性迁移：从邮件版的 state.json 导入初始快照")
    ap.add_argument("--source", action="append", help="只抓指定来源，可重复")
    args = ap.parse_args()

    conn = db.connect()
    db.init(conn)
    if args.from_state is not None:
        import_state_json(conn, args.from_state or None, verbose=True)
    else:
        refresh(conn, args.source, verbose=True)
    s = db.stats(conn)
    print("  库内合计 %d 条（在招 %d / 已下架 %d），收藏 %d"
          % (s["total"], s["open"], s["closed"], s["starred"]))
