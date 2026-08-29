# -*- coding: utf-8 -*-
"""桌面外壳：真正的窗口 + 系统托盘。

行为按需求设计：
  ✕ 关窗口   -> 只是隐藏到托盘，程序继续跑（并顺手后台抓一次）
  托盘左键   -> 把窗口叫回来
  托盘右键   -> 菜单里的「退出」才是真正关闭

界面本身还是 app.py 那套本地网页，这里只是套一层壳：
在后台线程里跑同一个 HTTP 服务，再用 WebView2 开一个没有地址栏的窗口指过去。

启动：python desktop.py     （或双击 启动.bat）
"""

import argparse
import ctypes
import socket
import sys
import threading
import time
from pathlib import Path

import webview
from PIL import Image
import pystray

import app as webapp
import db
import ingest

BASE_DIR = Path(__file__).resolve().parent
ICON_PATH = BASE_DIR / "app.ico"
ICON_PNG = BASE_DIR / "static" / "icon.png"

HOST = "127.0.0.1"
DEFAULT_PORT = 8765
APP_NAME = "Predoc Watcher"

# 隐藏到托盘后每隔多久自己抓一次
DEFAULT_INTERVAL_HOURS = 6


class Shell:
    def __init__(self, port, interval_hours):
        self.port = port
        self.interval = interval_hours * 3600
        self.window = None
        self.tray = None
        self.httpd = None
        self.quitting = False
        self.wake = threading.Event()      # 用来叫醒后台抓取线程
        self.announce_next = False         # 只有主动点「立即检查更新」才回报"没有新岗位"

    # ---------------------------------------------------------- HTTP 服务

    def start_server(self):
        from http.server import ThreadingHTTPServer
        self.httpd = ThreadingHTTPServer((HOST, self.port), webapp.Handler)
        t = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        t.start()

    @property
    def url(self):
        return "http://%s:%d/" % (HOST, self.port)

    # ---------------------------------------------------------- 窗口

    def on_closing(self):
        """✕ 不退出，只隐藏 —— 返回 False 取消真正的关闭。"""
        if self.quitting:
            return True
        self.window.hide()
        self.wake.set()                    # 顺手后台抓一次
        return False

    def show_window(self, *_):
        if self.window:
            self.window.show()
            self.window.restore()

    def register_show_endpoint(self):
        """让"再启动一次"能把已有窗口叫回来，而不是开出第二个实例。"""
        def api_show(conn, payload):
            self.show_window()
            return {"ok": True}
        webapp.APIS["/api/show"] = api_show

    # ---------------------------------------------------------- 托盘

    def notify(self, message, title=APP_NAME):
        try:
            if self.tray:
                self.tray.notify(message, title)
        except Exception:                                   # noqa: BLE001
            pass                                            # 通知失败不该影响主流程

    def build_tray(self):
        image = Image.open(ICON_PNG)
        menu = pystray.Menu(
            pystray.MenuItem("打开 %s" % APP_NAME, self.show_window, default=True),
            pystray.MenuItem("立即检查更新", self.check_now),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self.quit),
        )
        self.tray = pystray.Icon("predoc_watcher", image, APP_NAME, menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def check_now(self, *_):
        """托盘菜单里主动触发 —— 这种情况下没有新岗位也要回个话，
        否则你不知道它到底查没查。自动跑的那些则保持静默。"""
        self.announce_next = True
        self.wake.set()

    def quit(self, *_):
        self.quitting = True
        self.wake.set()
        try:
            if self.tray:
                self.tray.stop()
        except Exception:                                   # noqa: BLE001
            pass
        if self.httpd:
            self.httpd.shutdown()
        if self.window:
            self.window.destroy()

    # ---------------------------------------------------------- 后台抓取

    def fetch_loop(self):
        """隐藏时抓一次，之后每隔 interval 再抓。

        **只有真的发现新岗位才弹通知**，其余一律静默 —— 后台每隔几小时跑一次，
        每次都汇报"没有新岗位"是纯粹的打扰。唯一的例外是你从托盘主动点了
        「立即检查更新」，那种情况下不回话反而让人不确定它有没有执行。
        """
        while not self.quitting:
            self.wake.wait(timeout=self.interval)
            self.wake.clear()
            announce = self.announce_next
            self.announce_next = False
            if self.quitting:
                return
            conn = db.connect()
            try:
                r = ingest.refresh(conn)
            except Exception as exc:                        # noqa: BLE001
                conn.close()
                if announce:
                    self.notify("检查失败：%s" % exc)
                continue
            conn.close()
            if r["added"]:
                self.notify("发现 %d 个新岗位，点开看看" % r["added"])
            elif announce:
                failed = len(r["failures"])
                self.notify("没有新岗位" + ("（%d 个来源抓取失败）" % failed if failed else ""))


def already_running(port):
    """端口被占 = 已经有一个实例在跑。托盘程序很容易被重复启动。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((HOST, port)) == 0


def set_window_icon():
    """给窗口和任务栏挂上图标。

    pywebview 在 Windows 上不直接暴露设置图标的接口，所以用 Win32 消息发给
    自己的窗口句柄。失败也无所谓 —— 只是少个图标，不影响使用。
    """
    try:
        user32 = ctypes.windll.user32
        hicon = user32.LoadImageW(None, str(ICON_PATH), 1, 0, 0, 0x00000010)  # IMAGE_ICON|LOADFROMFILE
        if not hicon:
            return
        hwnd = user32.FindWindowW(None, APP_NAME)
        if hwnd:
            user32.SendMessageW(hwnd, 0x0080, 1, hicon)   # WM_SETICON, ICON_BIG
            user32.SendMessageW(hwnd, 0x0080, 0, hicon)   # WM_SETICON, ICON_SMALL
    except Exception:                                     # noqa: BLE001
        pass


def main():
    ap = argparse.ArgumentParser(description="%s 桌面版" % APP_NAME)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--interval", type=float, default=DEFAULT_INTERVAL_HOURS,
                    help="后台自动检查的间隔（小时），默认 %d" % DEFAULT_INTERVAL_HOURS)
    ap.add_argument("--no-fetch", action="store_true", help="启动时不抓取")
    ap.add_argument("--minimized", action="store_true", help="启动后直接缩到托盘")
    args = ap.parse_args()

    if already_running(args.port):
        # 已经有一个实例了 —— 把它的窗口叫回来，而不是开第二个。
        try:
            import urllib.request
            urllib.request.urlopen(
                urllib.request.Request("http://%s:%d/api/show" % (HOST, args.port),
                                       data=b"{}",
                                       headers={"Content-Type": "application/json"}),
                timeout=3).read()
            print("%s 已在运行，已把窗口叫回前台。" % APP_NAME)
        except Exception:                                 # noqa: BLE001
            print("%s 已在运行。点任务栏右下角的托盘图标即可打开。" % APP_NAME)
        return 0

    # 任务栏图标要正确，得先声明自己的 AppUserModelID，否则会挂在 python.exe 名下
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ruan.predoc.watcher")
    except Exception:                                     # noqa: BLE001
        pass

    conn = db.connect()
    db.init(conn)
    if not args.no_fetch:
        try:
            r = ingest.refresh(conn)
            print("启动检查：新增 %d · 在招 %d" % (r["added"], r["total"]))
        except Exception as exc:                          # noqa: BLE001
            print("启动检查失败（不影响浏览已有数据）：%s" % exc)
    conn.close()

    shell = Shell(args.port, args.interval)
    shell.register_show_endpoint()
    shell.start_server()
    shell.build_tray()
    threading.Thread(target=shell.fetch_loop, daemon=True).start()

    shell.window = webview.create_window(
        APP_NAME, shell.url, width=1180, height=860, min_size=(720, 560),
        hidden=args.minimized,
    )
    shell.window.events.closing += shell.on_closing

    def after_start():
        time.sleep(0.6)                                   # 等窗口真正建出来再挂图标
        set_window_icon()

    print("%s 已启动。关闭窗口只会缩到托盘，右键托盘图标可退出。" % APP_NAME)
    webview.start(after_start)
    shell.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main())
