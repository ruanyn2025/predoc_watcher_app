# -*- coding: utf-8 -*-
"""界面文案的中英两版。

所有能被用户看到的字符串都集中在这里，模板和前端都从这里取 —— 散在各处的话
加一门语言就得翻遍全项目。带 {} 的是格式串，参数名见调用处。

语言选择存在数据库的 meta 表里，所以关掉软件再开还是上次那门语言。
"""

from datetime import datetime

DEFAULT_LANG = "zh"
LANGS = ("zh", "en")

S = {
    # ---- 顶栏与导航
    "nav.new":        ("新增", "New"),
    "nav.history":    ("历史列表", "All Jobs"),
    "nav.starred":    ("收藏夹", "Starred"),
    "nav.calendar":   ("日历", "Calendar"),
    "nav.counts":     ("在招 {open} · 已下架 {closed}", "{open} open · {closed} closed"),
    "nav.refresh":    ("刷新", "Refresh"),
    "nav.lang_hint":  ("Switch to English", "切换为中文"),

    # ---- 岗位卡片
    "card.untitled":  ("（无标题）", "(untitled)"),
    "card.star":      ("收藏并设提醒", "Star and set a reminder"),
    "card.unstar":    ("取消收藏", "Remove from starred"),
    "card.seen":      ("抓取于 {date}", "Found {date}"),
    "card.seen_hint": ("本软件首次抓取到这条岗位的日期",
                       "When this app first saw this posting"),
    "card.closed":    ("已下架", "Delisted"),
    "card.remind":    ("提醒 {date}", "Reminder {date}"),
    # 括号也随语言走：中文用全角，英文用半角并带前导空格
    "card.today":     ("（今天）", " (today)"),
    "card.left":      ("（剩余 {n} 天）", " ({n} day left)| ({n} days left)"),
    "card.overdue":   ("（逾期 {n} 天）", " ({n} day overdue)| ({n} days overdue)"),
    "card.institution": ("机构", "Institution"),
    "card.researchers": ("导师", "Researchers"),
    "card.fields":    ("领域", "Fields"),
    "card.deadline":  ("截止", "Deadline"),
    "card.note":      ("备注", "Note"),

    # ---- 首页
    "index.title":    ("新增", "New"),
    "index.upcoming": ("即将到期", "Due soon"),
    "index.upcoming_sub": ("·未来7天", "· next 7 days"),
    "index.unread":   ("未读 {n} 条", "{n} unread"),
    "index.none":     ("没有新增岗位", "No new postings"),
    "index.mark_read": ("全部标为已读", "Mark all read"),
    "index.day_group": ("{day} 新增 {n} 条", "{day} — {n} new"),
    "index.footer":   ("最近一次同步 {date} · 共 {open} 个在招 · ",
                       "Last checked {date} · {open} open · "),

    # ---- 历史列表
    "history.title":  ("历史列表", "All Jobs"),
    "history.search_ph": ("搜领域 / 导师 / 学校学院，空格分隔多个关键词",
                          "Search fields, researchers, institutions — space-separated"),
    "history.all_sources": ("全部来源", "All sources"),
    "history.any_status": ("在招 + 已下架", "Open + delisted"),
    "history.open_only": ("只看在招", "Open only"),
    "history.closed_only": ("只看已下架", "Delisted only"),
    "history.by_seen": ("按抓取时间", "By date found"),
    "history.by_title": ("按标题", "By title"),
    "history.by_inst": ("按机构", "By institution"),
    "history.filter": ("筛选", "Filter"),
    "history.clear":  ("清空", "Clear"),
    "history.count":  ("{n} 条结果", "{n} result|{n} results"),
    "history.empty":  ("没有匹配的岗位，换个词试试", "Nothing matched — try another word"),

    # ---- 收藏夹
    "starred.title":  ("收藏夹", "Starred"),
    "starred.sub":    ("按提醒日期排序", "sorted by reminder date"),
    "starred.empty":  ("还没有收藏。在首页或历史列表里点 ☆ 收藏岗位，并设一个提醒日期。",
                       "Nothing starred yet. Hit ☆ on any posting to save it and set a reminder."),
    "starred.done":   ("已处理", "Handled"),
    "starred.done_n": ("{n} 个", "{n}"),

    # ---- 日历
    "cal.title":      ("{year} 年 {month} 月", "{month_name} {year}"),
    "cal.count":      ("本月 {n} 个提醒", "{n} reminder this month|{n} reminders this month"),
    "cal.prev":       ("← 上月", "← Prev"),
    "cal.this":       ("本月", "Today"),
    "cal.next":       ("下月 →", "Next →"),
    "cal.note":       ("日历显示已收藏岗位的提醒。提醒日期在收藏时设定，可在",
                       "The calendar shows reminders for starred postings. Dates are set when you star, and can be changed in "),
    "cal.note_tail":  ("中修改。", "."),

    # ---- 收藏面板（前端）
    "modal.title":    ("加入收藏并设置提醒", "Star and set a reminder"),
    "modal.deadline": ("招聘截止日期：", "Application deadline: "),
    "modal.none":     ("暂无", "not stated"),
    "modal.date":     ("提醒日期", "Remind me on"),
    "modal.note":     ("备注（可选）", "Note (optional)"),
    "modal.note_ph":  ("比如：需要两封推荐信", "e.g. needs two reference letters"),
    "modal.cancel":   ("取消", "Cancel"),
    "modal.confirm":  ("确认收藏", "Save"),
    "modal.before_n": ("提前 {n} 天", "{n} days before"),
    "modal.on_deadline": ("就在截止日", "On the deadline"),
    "modal.in_n":     ("{n} 天后", "In {n} days"),

    # ---- 提示条（前端）
    "toast.unstarred": ("已取消收藏", "Removed from starred"),
    "toast.error":    ("出错了", "Something went wrong"),
    "toast.save_fail": ("保存失败", "Could not save"),
    "toast.starred":  ("已收藏·将于{date}提醒", "Starred · reminder {date}"),
    "toast.starred_no_date": ("已收藏·未设提醒", "Starred · no reminder"),
    "toast.checking": ("检查中…", "Checking…"),
    "toast.fetch_fail": ("抓取失败：", "Check failed: "),
    "toast.result":   ("新增 {added} · 下架 {closed} · 在招 {total}",
                       "{added} new · {closed} delisted · {total} open"),
    "toast.some_failed": ("（{n} 个来源抓取失败）", " ({n} sources failed)"),

    # ---- 来源名
    "src.predoc":         ("predoc.org", "predoc.org"),
    "src.nber":           ("NBER（本部）", "NBER (internal)"),
    "src.nber_external":  ("NBER（非本部）", "NBER (external)"),
}

WEEKDAYS = (
    ("周一", "周二", "周三", "周四", "周五", "周六", "周日"),
    ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
)

MONTHS_EN = ("January", "February", "March", "April", "May", "June", "July",
             "August", "September", "October", "November", "December")


def normalise(lang):
    return lang if lang in LANGS else DEFAULT_LANG


def t(key, lang=DEFAULT_LANG, **kw):
    """取一条文案。

    英文串里用 | 分隔单数|复数（中文没有这个问题，所以只在英文侧写）。
    按传进来的 n 选一边。
    """
    pair = S.get(key)
    if pair is None:
        return key                              # 缺翻译时把键名露出来，便于发现
    text = pair[0 if normalise(lang) == "zh" else 1]
    if "|" in text:
        one, many = text.split("|", 1)
        text = one if kw.get("n") == 1 else many
    return text.format(**kw) if kw else text


def fdate(value, lang=DEFAULT_LANG):
    """卡片和徽章上的短日期。"""
    if not value:
        return ""
    try:
        d = datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except ValueError:
        return str(value)
    return d.strftime("%m月%d日") if normalise(lang) == "zh" else d.strftime("%b %d")


def weekdays(lang=DEFAULT_LANG):
    return WEEKDAYS[0 if normalise(lang) == "zh" else 1]


def month_name(month, lang=DEFAULT_LANG):
    return str(month) if normalise(lang) == "zh" else MONTHS_EN[month - 1]


def source_label(source_id, lang=DEFAULT_LANG):
    return t("src." + source_id, lang)


def js_strings(lang):
    """前端要用到的那部分，注入页面供 app.js 取用。"""
    keys = [k for k in S if k.startswith(("modal.", "toast."))]
    return {k: S[k][0 if normalise(lang) == "zh" else 1] for k in keys}
