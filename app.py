# -*- coding: utf-8 -*-
"""predoc 岗位浏览器 —— 本地小软件。

刻意不依赖 Flask：只用标准库 http.server + 已有的 jinja2 + sqlite3，
这样不必往 conda 环境里装任何新包，换台机器复制文件夹就能跑。

启动：python app.py  （自动打开浏览器）
"""

import argparse
import json
import mimetypes
import re
import sys
import threading
import webbrowser
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from jinja2 import Environment, FileSystemLoader, select_autoescape

import db
import deadlines
import i18n
import ingest

BASE_DIR = Path(__file__).resolve().parent
HOST, PORT = "127.0.0.1", 8765

env = Environment(
    loader=FileSystemLoader(str(BASE_DIR / "templates")),
    autoescape=select_autoescape(["html"]),
)


def _days_until(value):
    try:
        d = datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None
    return (d - date.today()).days


env.filters["days_until"] = _days_until


def render(name, **ctx):
    conn = ctx.pop("conn", None)
    lang = ctx.get("lang") or i18n.DEFAULT_LANG
    if conn is not None:
        ctx.setdefault("stats", db.stats(conn))
    ctx.setdefault("today", date.today())
    ctx["lang"] = lang
    ctx["t"] = lambda key, **kw: i18n.t(key, lang, **kw)
    ctx["fdate"] = lambda v: i18n.fdate(v, lang)
    ctx["source_label"] = lambda sid: i18n.source_label(sid, lang)
    ctx["js_strings"] = json.dumps(i18n.js_strings(lang), ensure_ascii=False)
    ctx["lang_options"] = i18n.lang_options(lang)
    return env.get_template(name).render(**ctx).encode("utf-8")


def current_lang(conn):
    return i18n.normalise(db.get_meta(conn, "lang", i18n.DEFAULT_LANG))


def page_index(conn, query):
    lang = current_lang(conn)
    fresh = db.unread_jobs(conn)
    groups = []
    for job in fresh:
        if not groups or groups[-1]["day"] != job["first_seen"]:
            groups.append({"day": job["first_seen"], "jobs": []})
        groups[-1]["jobs"].append(job)

    horizon = (date.today() + timedelta(days=7)).isoformat()
    upcoming = [j for j in db.reminders_between(conn, "1970-01-01", horizon) if not j["done"]]

    return render("index.html", conn=conn, groups=groups, fresh_count=len(fresh),
                  upcoming=upcoming,
                  last_ingest=db.get_meta(conn, "last_fetch_at"),
                  initialized_on=db.get_meta(conn, "initialized_on"),
                  nav="index", lang=lang)


def page_history(conn, query):
    lang = current_lang(conn)
    q = (query.get("q", [""])[0] or "").strip()
    source = query.get("source", [""])[0]
    status = query.get("status", [""])[0]
    order = query.get("order", ["first_seen"])[0]
    jobs = db.search_jobs(conn, q=q, source=source, status=status, order=order, limit=1000)
    return render("history.html", conn=conn, jobs=jobs, q=q, source=source,
                  status=status, order=order, count=len(jobs),
                  source_ids=list(db.SOURCE_LABELS), nav="history", lang=lang)


def page_starred(conn, query):
    lang = current_lang(conn)
    jobs = db.starred_jobs(conn)
    return render("starred.html", conn=conn, jobs=jobs,
                  active=[j for j in jobs if not j["done"]],
                  done=[j for j in jobs if j["done"]], nav="starred", lang=lang)


def page_calendar(conn, query):
    lang = current_lang(conn)
    ym = query.get("ym", [""])[0] or date.today().strftime("%Y-%m")
    try:
        year, month = (int(x) for x in ym.split("-"))
        first = date(year, month, 1)
    except (ValueError, TypeError):
        first = date.today().replace(day=1)
        year, month = first.year, first.month

    nxt = date(year + (month == 12), month % 12 + 1, 1)
    last = nxt - timedelta(days=1)
    by_day = {}
    for j in db.reminders_between(conn, first.isoformat(), last.isoformat()):
        by_day.setdefault(j["remind_on"], []).append(j)

    start = first - timedelta(days=first.weekday())
    weeks, cur = [], start
    while True:
        week = []
        for _ in range(7):
            week.append({"date": cur, "in_month": cur.month == month,
                         "jobs": by_day.get(cur.isoformat(), [])})
            cur += timedelta(days=1)
        weeks.append(week)
        if cur > last:
            break

    prev_m = first - timedelta(days=1)
    return render("calendar.html", conn=conn, weeks=weeks, year=year, month=month,
                  prev_ym=prev_m.strftime("%Y-%m"), next_ym=nxt.strftime("%Y-%m"),
                  this_ym=date.today().strftime("%Y-%m"),
                  total=sum(len(v) for v in by_day.values()), nav="calendar", lang=lang,
                  weekdays=i18n.weekdays(lang), month_name=i18n.month_name(month, lang))


def api_suggest(conn, payload):
    """收藏面板打开时调用：给出预填日期和理由。"""
    job = db.get_job(conn, payload["key"])
    if not job:
        return {"ok": False, "error": "岗位不存在"}
    remind, info, basis = deadlines.suggest(job["deadline_raw"])
    return {"ok": True, "remind_on": remind.isoformat(), "basis": basis,
            "label": info["label"], "kind": info["kind"],
            "deadline_raw": job["deadline_raw"] or "",
            "parsed": info["date"].isoformat() if info["date"] else None}


def api_star(conn, payload):
    key = payload["key"]
    if not db.get_job(conn, key):
        return {"ok": False, "error": "岗位不存在"}
    remind_on = (payload.get("remind_on") or "").strip() or None
    if remind_on and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", remind_on):
        return {"ok": False, "error": "日期格式应为 YYYY-MM-DD"}
    db.star(conn, key, remind_on, payload.get("basis") or "manual", payload.get("note") or "")
    return {"ok": True}


def api_unstar(conn, payload):
    db.unstar(conn, payload["key"])
    return {"ok": True}


def api_done(conn, payload):
    db.set_done(conn, payload["key"], bool(payload.get("done")))
    return {"ok": True}


def api_lang(conn, payload):
    """切换界面语言。存进 meta，所以下次打开还是这门语言。"""
    db.set_meta(conn, "lang", i18n.normalise(payload.get("lang")))
    conn.commit()
    return {"ok": True}


def api_mark_read(conn, payload):
    return {"ok": True, "cleared": db.mark_all_read(conn)}


def api_refresh(conn, payload):
    """现场访问三个网站，抓取最新岗位。"""
    try:
        return {"ok": True, "result": ingest.refresh(conn)}
    except Exception as exc:                                  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


PAGES = {"/": page_index, "/history": page_history,
         "/starred": page_starred, "/calendar": page_calendar}
APIS = {"/api/lang": api_lang, "/api/suggest": api_suggest, "/api/star": api_star, "/api/unstar": api_unstar,
        "/api/done": api_done, "/api/mark-read": api_mark_read, "/api/refresh": api_refresh}


class Handler(BaseHTTPRequestHandler):
    server_version = "PredocBrowser"

    def log_message(self, fmt, *args):
        if "--verbose" in sys.argv:
            super().log_message(fmt, *args)

    def _send(self, body, status=200, ctype="text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status=200):
        self._send(json.dumps(obj, ensure_ascii=False).encode("utf-8"),
                   status, "application/json; charset=utf-8")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path.startswith("/static/"):
            f = (BASE_DIR / path.lstrip("/")).resolve()
            if f.is_file() and BASE_DIR in f.parents:
                ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
                self._send(f.read_bytes(), 200, ctype)
            else:
                self._send(b"not found", 404, "text/plain; charset=utf-8")
            return

        handler = PAGES.get(path)
        if not handler:
            self._send("<h1>404</h1><p><a href='/'>回首页</a></p>".encode("utf-8"), 404)
            return

        conn = db.connect()
        try:
            self._send(handler(conn, parse_qs(parsed.query)))
        finally:
            conn.close()

    def do_POST(self):
        path = urlparse(self.path).path
        handler = APIS.get(path)
        if not handler:
            self._json({"ok": False, "error": "未知接口"}, 404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self._json({"ok": False, "error": "请求体不是合法 JSON"}, 400)
            return
        conn = db.connect()
        try:
            self._json(handler(conn, payload))
        except Exception as exc:                              # noqa: BLE001
            self._json({"ok": False, "error": str(exc)}, 500)
        finally:
            conn.close()


def main():
    ap = argparse.ArgumentParser(description="predoc 岗位浏览器")
    ap.add_argument("--port", type=int, default=PORT)
    ap.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    ap.add_argument("--no-fetch", action="store_true", help="启动时不抓取，直接用库里已有的数据")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    conn = db.connect()
    db.init(conn)
    if not args.no_fetch:
        print("正在检查三个来源…")
        try:
            r = ingest.refresh(conn, verbose=True)
            for sid, err in r["failures"].items():
                print("  ! %s 抓取失败：%s" % (ingest.fetch.SOURCE_BY_ID[sid]["name"], err))
        except Exception as exc:                              # noqa: BLE001
            print("抓取失败（不影响浏览库里已有的岗位）：%s" % exc)
    conn.close()

    url = "http://%s:%d/" % (HOST, args.port)
    httpd = ThreadingHTTPServer((HOST, args.port), Handler)
    print("岗位浏览器已启动：%s" % url)
    print("关闭这个窗口即可停止。")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
