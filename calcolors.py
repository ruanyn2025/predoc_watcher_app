# -*- coding: utf-8 -*-
"""日历两类标记的可自定义配色。

用户只挑一个主色，深浅两套的「实心 / 浅底 / 文字」三档由这里推导出来 ——
让人去调六个值既麻烦又容易调出读不清的组合。

推导规则：
  solid = 用户选的色，直接作近期标记的底色
  soft  = 往当前表面色兑水，作远期标记的浅底
  text  = 调整明度直到在对应底色上够读
"""

PRESETS = [
    ("red",    "#e03131"),
    ("orange", "#ef7c14"),
    ("yellow", "#e3b505"),
    ("green",  "#2f9e44"),
    ("cyan",   "#0c8599"),
    ("blue",   "#2563eb"),
    ("purple", "#7048e8"),
]

DEFAULTS = {"remind": "#e3b505", "event": "#2563eb"}

LIGHT_SURFACE = (255, 255, 255)
DARK_SURFACE = (21, 21, 24)


def parse(text, fallback="#2563eb"):
    """接受 #rgb / #rrggbb / rrggbb，认不出就退回默认值。"""
    t = (text or "").strip().lstrip("#")
    if len(t) == 3 and all(c in "0123456789abcdefABCDEF" for c in t):
        t = "".join(c * 2 for c in t)
    if len(t) != 6 or not all(c in "0123456789abcdefABCDEF" for c in t):
        return fallback
    return "#" + t.lower()


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def _hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def _mix(a, b, t):
    """a 占 t，b 占 1-t。"""
    return tuple(a[i] * t + b[i] * (1 - t) for i in range(3))


def _lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _readable(base, surface, target=4.0):
    """把 base 往黑或往白推，直到在 surface 上达到 target 对比度。"""
    toward = (0, 0, 0) if _lum(surface) > 0.5 else (255, 255, 255)
    best = base
    for i in range(21):
        cand = _mix(base, toward, 1 - i * 0.045)
        best = cand
        if contrast(cand, surface) >= target:
            break
    return best


def derive(base_hex):
    """给一个主色，算出深浅两套各三档。"""
    base = _rgb(parse(base_hex))
    out = {}
    for name, surface in (("light", LIGHT_SURFACE), ("dark", DARK_SURFACE)):
        soft_ratio = 0.16 if name == "light" else 0.26
        out[name] = {
            "solid": _hex(base),
            "soft": _hex(_mix(base, surface, soft_ratio)),
            "text": _hex(_readable(base, surface)),
            # 实心底上压什么字：底色亮就用近黑，暗就用白
            "on": "#2b2200" if _lum(base) > 0.45 else "#ffffff",
        }
    return out


def css_vars(colors):
    """colors: {'remind': '#..', 'event': '#..'} -> 两段 CSS 变量声明。"""
    blocks = {}
    for scheme in ("light", "dark"):
        parts = []
        for kind, base in colors.items():
            d = derive(base)[scheme]
            parts.append(
                "--cal-%s-solid:%s;--cal-%s-soft:%s;--cal-%s:%s;--cal-%s-on:%s;"
                % (kind, d["solid"], kind, d["soft"], kind, d["text"], kind, d["on"]))
        blocks[scheme] = "".join(parts)
    return blocks


def current(get_meta):
    return {k: parse(get_meta("cal_color_" + k, v), v) for k, v in DEFAULTS.items()}
