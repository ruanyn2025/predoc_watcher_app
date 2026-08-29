# -*- coding: utf-8 -*-
"""自带的抓取与解析 —— 本软件不依赖邮件推送版。

解析逻辑与 ../mailer/watch_jobs.py 同源，但**是独立的一份拷贝**：两边互不 import，
邮件版停用、删除、改动都不影响这里。代价是站点改版时两处都要改（若邮件版已停用，
就只需要改这里）。

主键配方必须与邮件版完全一致，否则切换过来时库里已有的岗位会被当成"新增"全量刷屏。
"""

import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
EXTRA_CA_DIR = BASE_DIR / "extra_ca"
CA_BUNDLE_PATH = BASE_DIR / ".ca_bundle.pem"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


class ParseError(Exception):
    """页面结构与预期不符 —— 视为抓取失败，绝不当成『0 条岗位』。"""


# -------------------------------------------------------------- 文本归一化

def norm_space(s):
    """压缩空白、去掉 &nbsp;。"""
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def norm_key(s):
    """构造主键用：小写 + 压空白 + 去首尾标点。"""
    return norm_space(s).lower().strip(" .,;:-_/|")


def norm_label(s):
    """标签模糊匹配：只留小写字母数字。

    这样 'Field(s) of Research'、'Fields of Research'、'Field(s0 of research'
    （站方错字）、'NBER Sponsoring Researcher)s)' 都能被同一条规则命中。
    """
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


LABEL_RULES = (
    ("deadline", "deadline"),
    ("researcher", "researchers"),
    ("institution", "institution"),
    ("field", "fields"),
    ("location", "location"),
    ("startdate", "start_date"),
    ("visa", "visa"),
)

_LABEL_PHRASE = (
    r"(?:nber[\s\-]*)?sponsoring[\s\-]*researchers?\s*[\(\)s0-9]{0,5}"
    r"|(?:nber[\s\-]*)?sponsoring[\s\-]*institutions?"
    r"|institutions?"
    r"|fields?\s*[\(\)s0-9]{0,5}\s*of\s+research"
    r"|fields?\s*\(\s*s[0-9\)]*\)?"
    r"|deadlines?"
    r"|start\s+date"
)

# 站方偶尔漏 <br>，两个字段挤在一行，在行内的「标签 + 冒号」处切开。
RE_EMBEDDED_LABEL = re.compile(r"(?i)\s+(?=(?:%s)\s*[:：])" % _LABEL_PHRASE)
# 站方偶尔漏冒号，只在行首匹配且标签后必须还有内容。
RE_LABEL_NO_COLON = re.compile(r"(?i)^\s*(%s)\s+(?=\S)" % _LABEL_PHRASE)


def split_embedded(value):
    parts = RE_EMBEDDED_LABEL.split(value, maxsplit=1)
    if len(parts) == 2:
        return norm_space(parts[0]), parts[1].strip()
    return value, None


def _match_field(label_text):
    n = norm_label(label_text)
    for needle, field in LABEL_RULES:
        if needle in n:
            return field
    return None


def split_label(line):
    """'Institution: MIT' -> ('institution', 'MIT')；认不出返回 (None, line)。"""
    m = re.match(r"\s*([^:：]{1,60}?)\s*[:：]\s*(.*)$", line, re.S)
    if m:
        field = _match_field(m.group(1))
        if field:
            return field, norm_space(m.group(2))
    m = RE_LABEL_NO_COLON.match(line)
    if m:
        field = _match_field(m.group(1))
        if field:
            return field, norm_space(line[m.end():])
    return None, line


def block_text(node):
    """按 <br> 分行取纯文本。

    必须用无分隔符的 get_text()：若用 get_text("\n")，BeautifulSoup 会在每两个内联
    子节点间插换行，'<strong>Deadline</strong>: Rolling' 会被拆成两行，字段就丢了。
    """
    if node is None:
        return ""
    for br in node.find_all("br"):
        br.replace_with("\n")
    raw = node.get_text().replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in raw.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def parse_meta_lines(lines):
    """解析元信息行；认不出的行收进 notes 而不是丢弃。"""
    out = {}
    notes = []
    pending = None
    queue = list(lines)
    while queue:
        ln = queue.pop(0)
        if not ln.strip():
            continue
        field, value = split_label(ln)
        if field:
            value, tail = split_embedded(value)
            if tail:
                queue.insert(0, tail)
            if value:
                out.setdefault(field, value)
                pending = None
            else:
                pending = field
        elif pending:
            out.setdefault(pending, norm_space(ln))
            pending = None
        else:
            notes.append(norm_space(ln))
    if notes:
        out["notes"] = " / ".join(notes)
    return out


def item_key(source_id, item):
    """复合主键：来源 + 链接 + 标题 + 机构 + 导师。

    NBER 页面上有 11 个链接被多条不同岗位共用，所以不能只用 link 去重。导师也必须
    进主键 —— Wharton 那条同链接、同标题、同机构的两个职位只有导师不同。
    刻意不含 fields：那是最容易被站方随手改动的字段。

    ⚠ 这个配方与 mailer/watch_jobs.py 的 item_key 必须逐字一致。
    """
    raw = "|".join([
        source_id,
        item.get("link", ""),
        norm_key(item.get("title", "")),
        norm_key(item.get("institution", "")),
        norm_key(item.get("researchers", "")),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


# -------------------------------------------------------------- 解析器

def parse_predoc(page_html, page_url):
    """predoc.org —— Sitecore 服务端渲染，每条岗位是一个 <article class="... sorted ...">。"""
    soup = BeautifulSoup(page_html, "html.parser")

    # 分类标签的显示名直接从页面自带的筛选下拉框里读，站方加新领域也不会漏。
    taxonomy = {}
    for sel in soup.find_all("select", attrs={"data-filter-group": True}):
        for opt in sel.find_all("option"):
            value = (opt.get("value") or "").lstrip(".").strip()
            label = norm_space(opt.get_text())
            if value and value != "all":
                taxonomy[value] = label

    articles = [a for a in soup.find_all("article") if "sorted" in (a.get("class") or [])]
    if not articles:
        raise ParseError("未找到 article.sorted —— 页面结构可能已改版")

    items = []
    for art in articles:
        h2 = art.find("h2")
        anchor = h2.find("a", href=True) if h2 else None
        if not anchor:
            continue
        link = urljoin(page_url, anchor["href"].strip())
        title = norm_space(anchor.get_text())
        if not title:
            continue

        para = art.select_one(".swiss-text p") or art.find("p")
        raw_meta = block_text(para)
        item = parse_meta_lines(raw_meta.split("\n")) if raw_meta else {}
        item.update(title=title, link=link, raw_meta=raw_meta)

        classes = [c for c in (art.get("class") or []) if c not in ("all", "sorted")]
        item["tags"] = [taxonomy.get(c, c) for c in classes]
        items.append(item)
    return items


def parse_nber(page_html, page_url):
    """两个 NBER 页 —— Drupal 富文本，岗位是 'Available Positions' 之后的一串 <p>。"""
    soup = BeautifulSoup(page_html, "html.parser")
    root = soup.find("main") or soup

    heading = None
    for tag in root.find_all(["h1", "h2", "h3", "h4"]):
        if "availableposition" in norm_label(tag.get_text()):
            heading = tag
            break
    if heading is None:
        raise ParseError("未找到 'Available Positions' 标题 —— 页面结构可能已改版")

    items = []
    for para in heading.find_all_next("p"):
        anchors = [
            a for a in para.find_all("a", href=True)
            if not a["href"].strip().lower().startswith("mailto:")
        ]
        if not anchors:
            continue

        raw_meta = block_text(para)
        # 必须看到 Institution 标签才算一条岗位，否则是正文说明段落。
        if not any(split_label(ln)[0] == "institution" for ln in raw_meta.split("\n")):
            continue

        # href 可能带前导空格，也可能是 /sites/... 相对路径。
        link = urljoin(page_url, anchors[-1]["href"].strip())

        lines = raw_meta.split("\n")
        title = norm_space(lines[0])
        if not title:
            continue
        link_texts = set(norm_key(a.get_text()) for a in anchors)
        rest = [ln for ln in lines[1:] if norm_key(ln) not in link_texts]

        item = parse_meta_lines(rest)
        item.update(title=title, link=link, raw_meta=raw_meta, tags=[])
        items.append(item)
    return items


SOURCES = [
    {"id": "predoc", "name": "predoc.org",
     "url": "https://www.predoc.org/opportunities",
     "parser": parse_predoc, "min_count": 20},
    {"id": "nber", "name": "NBER（本部）",
     "url": "https://www.nber.org/career-resources/research-assistant-positions-nber",
     "parser": parse_nber, "min_count": 0},   # 该页常年可能是 0 条，空是合法状态
    {"id": "nber_external", "name": "NBER（非本部）",
     "url": "https://www.nber.org/career-resources/research-assistant-positions-not-nber",
     "parser": parse_nber, "min_count": 30},
]
SOURCE_BY_ID = {s["id"]: s for s in SOURCES}


# -------------------------------------------------------------- 网络

_ca_bundle_cache = []


def ca_bundle():
    """certifi 根证书 + extra_ca/ 下的中间证书，合成一份 CA bundle。

    predoc.org 只发了叶子证书、漏发 GoDaddy 中间证书。浏览器和 curl 能打开是因为
    Windows 会按证书的 AIA 字段自动补下载，OpenSSL/Python 不做这件事，于是报
    CERTIFICATE_VERIFY_FAILED。正确解法是把中间证书随项目带上，而不是关掉校验 ——
    证书校验始终是开着的。
    """
    if _ca_bundle_cache:
        return _ca_bundle_cache[0]

    extras = sorted(EXTRA_CA_DIR.glob("*.pem")) if EXTRA_CA_DIR.is_dir() else []
    if not extras:
        _ca_bundle_cache.append(True)
        return True

    try:
        import certifi
        chunks = [Path(certifi.where()).read_text(encoding="utf-8")]
    except Exception:
        chunks = []
    for pem in extras:
        chunks.append(pem.read_text(encoding="utf-8"))
    CA_BUNDLE_PATH.write_text("\n".join(chunks), encoding="utf-8")
    _ca_bundle_cache.append(str(CA_BUNDLE_PATH))
    return str(CA_BUNDLE_PATH)


def http_get(url, retries=3, timeout=30):
    last = None
    for attempt in range(retries):
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
                timeout=timeout,
                verify=ca_bundle(),
            )
            resp.raise_for_status()
            if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
                resp.encoding = resp.apparent_encoding or "utf-8"
            return resp.text
        except Exception as exc:                                  # noqa: BLE001
            last = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
    raise last


def collect(source):
    """抓取并解析单个来源。任一来源失败不影响其他来源。

    最少条数护栏防的是这种事：站方改版导致解析出 0 条，若当成"岗位全下架了"，
    库里的岗位会被批量标为已下架，等站方恢复又全部变成"新增"轰炸一遍。
    """
    try:
        page = http_get(source["url"])
        items = source["parser"](page, source["url"])
        if len(items) < source["min_count"]:
            raise ParseError("只解析出 %d 条，低于下限 %d 条 —— 疑似解析异常"
                             % (len(items), source["min_count"]))
        return {"ok": True, "items": items, "error": None}
    except Exception as exc:                                      # noqa: BLE001
        return {"ok": False, "items": [], "error": str(exc)}


def collect_all(source_ids=None):
    """抓取全部（或指定的）来源，返回 {source_id: {ok, items, error}}。"""
    out = {}
    for src in SOURCES:
        if source_ids and src["id"] not in source_ids:
            continue
        out[src["id"]] = collect(src)
    return out


if __name__ == "__main__":
    for sid, r in collect_all().items():
        name = SOURCE_BY_ID[sid]["name"]
        if r["ok"]:
            print("[%s] %d 条" % (name, len(r["items"])))
            for it in r["items"][:2]:
                print("    ", it.get("title", "")[:60], "|", it.get("institution", "")[:40])
        else:
            print("[%s] 失败：%s" % (name, r["error"]))
