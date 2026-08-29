# -*- coding: utf-8 -*-
"""从 predoc 的 deadline 原文里尽力抽出一个日期。

这个模块存在的唯一原因是数据很脏。对 208 条实测样本的分类：

    完全没有 deadline 字段        119 (57%)   —— 全部 116 条 NBER 岗位都没有
    纯 rolling / 无固定截止         50 (24%)
    只含日期                       21 (10%)
    rolling + 含日期                17  (8%)
    有文字但认不出日期                1  (0%)

而能抽出日期的 38 条里，11 条没写年份、19 条日期已过期。所以这里的目标不是
"自动算准"，而是"给出一个有依据的建议值 + 说明理由"，最终由用户在收藏时确认。
"""

import re
from datetime import date, timedelta

MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]
_ABBR = {m[:3]: i + 1 for i, m in enumerate(MONTHS)}
_FULL = {m: i + 1 for i, m in enumerate(MONTHS)}
_MONTH_ALT = "|".join(MONTHS + list(_ABBR))

# "October 15, 2026" / "Mar 1, 2026" / "April 1st, 2026" / "April 15"
_RE_MDY = re.compile(
    r"\b(" + _MONTH_ALT + r")\w*\.?\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*,?\s*(\d{4}))?",
    re.I,
)
# "20th April 2026"
_RE_DMY = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(" + _MONTH_ALT + r")\w*\.?(?:\s*,?\s*(\d{4}))?",
    re.I,
)
# "5/24/26" / "9/15/26" / "3/19/25"
_RE_SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b")

# 表示"没有硬性截止"的措辞。covers: Rolling / until filled / ongoing / ASAP / No deadline
_RE_ROLLING = re.compile(
    r"roll|until\s+(?:the\s+)?(?:all\s+)?positions?\s+(?:are\s+|is\s+)?filled"
    r"|until\s+filled|open\s+till|ongoing|continuous|as\s+needed"
    r"|no\s+deadline|asap|as\s+soon\s+as\s+possible",
    re.I,
)


def _month_num(word):
    w = word.lower()
    if w in _FULL:
        return _FULL[w]
    return _ABBR.get(w[:3])


def _resolve_year(month, day, year, today):
    """年份缺失时，选让这个日期落在未来的最近一年。

    数据里有 11 条只写了 "April 15" / "Feb 28" 这样的月日。站方显然指的是
    "下一个" 4月15日，所以补今年；今年的已经过了就补明年。
    """
    if year is not None:
        return year, True
    for candidate in (today.year, today.year + 1):
        try:
            if date(candidate, month, day) >= today:
                return candidate, False
        except ValueError:
            continue
    return today.year + 1, False


def _first_date(text, today):
    """按出现顺序找第一个日期。

    第一个通常就是起作用的那个：
      "Deadline is June 18, 2026, but we will review ... by June 2"  -> June 18
      "Rolling with priority deadline of August 2, 2026"             -> August 2
      "First review on 9/15/26, then rolling"                        -> 9/15
    """
    best = None  # (位置, 日期, 年份是否明写)
    for m in _RE_MDY.finditer(text):
        mo = _month_num(m.group(1))
        if not mo:
            continue
        day = int(m.group(2))
        yr, explicit = _resolve_year(mo, day, int(m.group(3)) if m.group(3) else None, today)
        try:
            d = date(yr, mo, day)
        except ValueError:
            continue
        if best is None or m.start() < best[0]:
            best = (m.start(), d, explicit)
    for m in _RE_DMY.finditer(text):
        mo = _month_num(m.group(2))
        if not mo:
            continue
        day = int(m.group(1))
        yr, explicit = _resolve_year(mo, day, int(m.group(3)) if m.group(3) else None, today)
        try:
            d = date(yr, mo, day)
        except ValueError:
            continue
        if best is None or m.start() < best[0]:
            best = (m.start(), d, explicit)
    for m in _RE_SLASH.finditer(text):
        mo, day, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if yr < 100:
            yr += 2000
        try:
            d = date(yr, mo, day)
        except ValueError:
            continue
        if best is None or m.start() < best[0]:
            best = (m.start(), d, True)
    return (best[1], best[2]) if best else (None, False)


def analyse(raw, today=None):
    """把一条 deadline 原文解析成结构化判断。

    返回 dict：
        kind        none | rolling | dated | dated_rolling
        date        抽出的日期（datetime.date）或 None
        year_explicit  年份是原文写明的还是推断的
        past        抽出的日期是否已过期
        label       给用户看的一句话解释
    """
    today = today or date.today()
    text = (raw or "").strip()
    if not text:
        return {"kind": "none", "date": None, "year_explicit": False, "past": False,
                "label": "原始数据没有截止日期字段"}

    d, explicit = _first_date(text, today)
    rolling = bool(_RE_ROLLING.search(text))

    if d is None:
        if rolling:
            return {"kind": "rolling", "date": None, "year_explicit": False, "past": False,
                    "label": "滚动招聘，无固定截止日期"}
        return {"kind": "none", "date": None, "year_explicit": False, "past": False,
                "label": "有文字说明但没能识别出日期"}

    past = d < today
    kind = "dated_rolling" if rolling else "dated"
    bits = []
    if not explicit:
        bits.append("原文没写年份，按最近的未来推断为 %d 年" % d.year)
    if past:
        bits.append("这个日期已经过去了")
    if rolling:
        bits.append("同时写了滚动招聘，日期可能只是优先审阅日")
    label = "；".join(bits) if bits else "原文给出了明确日期"
    return {"kind": kind, "date": d, "year_explicit": explicit, "past": past, "label": label}


def suggest(raw, today=None, rolling_days=7):
    """给出收藏时预填的提醒日期。

    规则：抽到未来的日期就用它；否则（滚动招聘 / 无字段 / 日期已过期）
    一律预填"今天 + rolling_days 天"。两种情况都会把理由带出去显示。
    """
    today = today or date.today()
    info = analyse(raw, today)
    if info["date"] and not info["past"]:
        return info["date"], info, "deadline"
    return today + timedelta(days=rolling_days), info, "rolling"
