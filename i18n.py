# -*- coding: utf-8 -*-
"""界面文案，五门语言。

所有能被用户看到的字符串都集中在这里，模板和前端都从这里取 —— 散在各处的话
加一门语言就得翻遍全项目。

每条是一个五元组，顺序严格对应 LANGS。文件末尾有一道自检，数错列会直接报错，
不会悄悄漏翻。

带 {} 的是格式串。英文/法语/西语的复数用 | 分隔（"{n} result|{n} results"），
按 n 自动选；中文没有这个问题，所以中文侧从不写 |。
"""

from datetime import datetime

#            简体      繁體        英        法        西
LANGS = ("zh", "zh-Hant", "en", "fr", "es")
DEFAULT_LANG = "zh"

# 语言自己的名字，不翻译 —— 选单里用母语显示才认得出
LANG_NAMES = {
    "zh": "简体中文", "zh-Hant": "繁體中文",
    "en": "English", "fr": "Français", "es": "Español",
}

S = {
    # ---- 顶栏与导航 ----------------------------------------------------
    "nav.new":        ("新增", "新增", "New", "Nouveautés", "Nuevas"),
    "nav.history":    ("历史列表", "歷史列表", "All Jobs", "Toutes les offres", "Todas las ofertas"),
    "nav.starred":    ("收藏夹", "收藏夾", "Starred", "Favoris", "Favoritos"),
    "nav.calendar":   ("日历", "日曆", "Calendar", "Calendrier", "Calendario"),
    "nav.counts":     ("在招 {open} · 已下架 {closed}", "在招 {open} · 已下架 {closed}",
                       "{open} open · {closed} closed", "{open} ouvertes · {closed} retirées",
                       "{open} abiertas · {closed} retiradas"),
    "nav.refresh":    ("刷新", "重新整理", "Refresh", "Actualiser", "Actualizar"),
    "nav.language":   ("语言", "語言", "Language", "Langue", "Idioma"),

    # ---- 岗位卡片 ------------------------------------------------------
    "card.untitled":  ("（无标题）", "（無標題）", "(untitled)", "(sans titre)", "(sin título)"),
    "card.star":      ("收藏并设提醒", "收藏並設提醒", "Star and set a reminder",
                       "Ajouter aux favoris et définir un rappel",
                       "Guardar y poner un recordatorio"),
    "card.unstar":    ("取消收藏", "取消收藏", "Remove from starred",
                       "Retirer des favoris", "Quitar de favoritos"),
    "card.edit":      ("编辑", "編輯", "Edit", "Modifier", "Editar"),
    "card.edit_hint": ("修改提醒日期和备注", "修改提醒日期和備註",
                       "Change the reminder date and note",
                       "Modifier la date de rappel et la note",
                       "Cambiar la fecha de recordatorio y la nota"),
    "card.seen":      ("抓取于 {date}", "抓取於 {date}", "Found {date}",
                       "Trouvée le {date}", "Encontrada el {date}"),
    "card.seen_hint": ("本软件首次抓取到这条岗位的日期", "本軟體首次抓取到這條職缺的日期",
                       "When this app first saw this posting",
                       "Quand l'application a vu cette offre pour la première fois",
                       "Cuándo esta aplicación vio esta oferta por primera vez"),
    "card.closed":    ("已下架", "已下架", "Delisted", "Retirée", "Retirada"),
    "card.remind":    ("提醒 {date}", "提醒 {date}", "Reminder {date}",
                       "Rappel {date}", "Recordatorio {date}"),
    # 括号也随语言走：中文用全角，西文用半角并带前导空格
    "card.today":     ("（今天）", "（今天）", " (today)", " (aujourd'hui)", " (hoy)"),
    "card.left":      ("（剩余 {n} 天）", "（剩餘 {n} 天）",
                       " ({n} day left)| ({n} days left)",
                       " ({n} jour restant)| ({n} jours restants)",
                       " (falta {n} día)| (faltan {n} días)"),
    "card.overdue":   ("（逾期 {n} 天）", "（逾期 {n} 天）",
                       " ({n} day overdue)| ({n} days overdue)",
                       " ({n} jour de retard)| ({n} jours de retard)",
                       " ({n} día de retraso)| ({n} días de retraso)"),
    "card.institution": ("机构", "機構", "Institution", "Institution", "Institución"),
    "card.researchers": ("导师", "指導教授", "Researchers", "Chercheurs", "Investigadores"),
    "card.fields":    ("领域", "領域", "Fields", "Domaines", "Áreas"),
    "card.deadline":  ("截止", "截止", "Deadline", "Date limite", "Fecha límite"),
    "card.note":      ("备注", "備註", "Note", "Note", "Nota"),

    # ---- 首页 ----------------------------------------------------------
    "index.title":    ("新增", "新增", "New", "Nouveautés", "Nuevas"),
    "index.upcoming": ("即将到期", "即將到期", "Due soon", "Bientôt échu", "Vence pronto"),
    "index.upcoming_sub": ("·未来7天", "·未來7天", " · next 7 days",
                           " · 7 prochains jours", " · próximos 7 días"),
    "index.unread":   ("未读 {n} 条", "未讀 {n} 條", "{n} unread",
                       "{n} non lue|{n} non lues", "{n} sin leer"),
    "index.none":     ("没有新增岗位", "沒有新增職缺", "No new postings",
                       "Aucune nouvelle offre", "No hay ofertas nuevas"),
    "index.mark_read": ("全部标为已读", "全部標為已讀", "Mark all read",
                        "Tout marquer comme lu", "Marcar todo como leído"),
    "index.day_group": ("{day} 新增 {n} 条", "{day} 新增 {n} 條", "{day} — {n} new",
                        "{day} — {n} nouvelle|{day} — {n} nouvelles",
                        "{day} — {n} nueva|{day} — {n} nuevas"),
    "index.footer":   ("最近一次同步 {date} · 共 {open} 个在招 · ",
                       "最近一次同步 {date} · 共 {open} 個在招 · ",
                       "Last checked {date} · {open} open · ",
                       "Dernière vérification {date} · {open} ouvertes · ",
                       "Última comprobación {date} · {open} abiertas · "),

    # ---- 历史列表 ------------------------------------------------------
    "history.title":  ("历史列表", "歷史列表", "All Jobs", "Toutes les offres", "Todas las ofertas"),
    "history.search_ph": ("搜领域 / 导师 / 学校学院，空格分隔多个关键词",
                          "搜領域 / 指導教授 / 學校學院，空格分隔多個關鍵詞",
                          "Search fields, researchers, institutions — space-separated",
                          "Domaines, chercheurs, institutions — séparés par des espaces",
                          "Áreas, investigadores, instituciones — separados por espacios"),
    "history.all_sources": ("全部来源", "全部來源", "All sources",
                            "Toutes les sources", "Todas las fuentes"),
    "history.any_status": ("在招 + 已下架", "在招 + 已下架", "Open + delisted",
                           "Ouvertes + retirées", "Abiertas + retiradas"),
    "history.open_only": ("只看在招", "只看在招", "Open only",
                          "Ouvertes seulement", "Solo abiertas"),
    "history.closed_only": ("只看已下架", "只看已下架", "Delisted only",
                            "Retirées seulement", "Solo retiradas"),
    "history.by_seen": ("按抓取时间", "按抓取時間", "By date found",
                        "Par date de découverte", "Por fecha de hallazgo"),
    "history.by_title": ("按标题", "按標題", "By title", "Par titre", "Por título"),
    "history.by_inst": ("按机构", "按機構", "By institution", "Par institution", "Por institución"),
    "history.filter": ("筛选", "篩選", "Filter", "Filtrer", "Filtrar"),
    "history.clear":  ("清空", "清空", "Clear", "Effacer", "Limpiar"),
    "history.count":  ("{n} 条结果", "{n} 條結果", "{n} result|{n} results",
                       "{n} résultat|{n} résultats", "{n} resultado|{n} resultados"),
    "history.empty":  ("没有匹配的岗位，换个词试试", "沒有符合的職缺，換個詞試試",
                       "Nothing matched — try another word",
                       "Aucun résultat — essayez un autre mot",
                       "Sin resultados — prueba otra palabra"),
}

S.update({
    # ---- 收藏夹 --------------------------------------------------------
    "starred.title":  ("收藏夹", "收藏夾", "Starred", "Favoris", "Favoritos"),
    "starred.sub":    ("按提醒日期排序", "按提醒日期排序", "sorted by reminder date",
                       "triés par date de rappel", "ordenados por fecha de recordatorio"),
    "starred.empty":  ("还没有收藏。在首页或历史列表里点 ☆ 收藏岗位，并设一个提醒日期。",
                       "還沒有收藏。在首頁或歷史列表裡點 ☆ 收藏職缺，並設一個提醒日期。",
                       "Nothing starred yet. Hit ☆ on any posting to save it and set a reminder.",
                       "Aucun favori. Cliquez sur ☆ sur une offre pour l'enregistrer et définir un rappel.",
                       "Sin favoritos. Pulsa ☆ en cualquier oferta para guardarla y poner un recordatorio."),
    "starred.done":   ("已处理", "已處理", "Handled", "Traités", "Gestionados"),
    "starred.done_n": ("{n} 个", "{n} 個", "{n}", "{n}", "{n}"),

    # ---- 日历 ----------------------------------------------------------
    "cal.title":      ("{year} 年 {month} 月", "{year} 年 {month} 月",
                       "{month_name} {year}", "{month_name} {year}", "{month_name} {year}"),
    "cal.count":      ("本月 {n} 个提醒", "本月 {n} 個提醒",
                       "{n} reminder this month|{n} reminders this month",
                       "{n} rappel ce mois-ci|{n} rappels ce mois-ci",
                       "{n} recordatorio este mes|{n} recordatorios este mes"),
    "cal.prev":       ("← 上月", "← 上月", "← Prev", "← Préc.", "← Ant."),
    "cal.this":       ("本月", "本月", "Today", "Ce mois", "Este mes"),
    "cal.next":       ("下月 →", "下月 →", "Next →", "Suiv. →", "Sig. →"),
    "cal.note":       ("日历显示已收藏岗位的提醒。提醒日期在收藏时设定，可在",
                       "日曆顯示已收藏職缺的提醒。提醒日期在收藏時設定，可在",
                       "The calendar shows reminders for starred postings. Dates are set when you star, and can be changed in ",
                       "Le calendrier affiche les rappels des offres en favori. Les dates sont définies à l'ajout et modifiables dans ",
                       "El calendario muestra recordatorios de las ofertas guardadas. Las fechas se fijan al guardar y se pueden cambiar en "),
    "cal.note_tail":  ("中修改。", "中修改。", ".", ".", "."),
})

S.update({
    # ---- 收藏面板（前端） ----------------------------------------------
    "modal.title":    ("加入收藏并设置提醒", "加入收藏並設定提醒", "Star and set a reminder",
                       "Ajouter aux favoris et définir un rappel", "Guardar y poner un recordatorio"),
    "modal.edit_title": ("编辑提醒", "編輯提醒", "Edit reminder",
                         "Modifier le rappel", "Editar recordatorio"),
    "modal.unstar":   ("取消收藏", "取消收藏", "Remove", "Retirer", "Quitar"),
    "modal.save":     ("保存", "儲存", "Save", "Enregistrer", "Guardar"),
    "modal.deadline": ("招聘截止日期：", "招聘截止日期：", "Application deadline: ",
                       "Date limite de candidature : ", "Fecha límite de solicitud: "),
    "modal.none":     ("暂无", "暫無", "not stated", "non précisée", "no indicada"),
    "modal.date":     ("提醒日期", "提醒日期", "Remind me on", "Me rappeler le", "Recordarme el"),
    "modal.note":     ("备注（可选）", "備註（可選）", "Note (optional)",
                       "Note (facultatif)", "Nota (opcional)"),
    "modal.note_ph":  ("比如：需要两封推荐信", "例如：需要兩封推薦信",
                       "e.g. needs two reference letters",
                       "p. ex. deux lettres de recommandation",
                       "p. ej. dos cartas de recomendación"),
    "modal.cancel":   ("取消", "取消", "Cancel", "Annuler", "Cancelar"),
    "modal.confirm":  ("确认收藏", "確認收藏", "Save", "Enregistrer", "Guardar"),
    "modal.before_n": ("提前 {n} 天", "提前 {n} 天", "{n} days before",
                       "{n} jours avant", "{n} días antes"),
    "modal.on_deadline": ("就在截止日", "就在截止日", "On the deadline",
                          "Le jour limite", "El día límite"),
    "modal.in_n":     ("{n} 天后", "{n} 天後", "In {n} days", "Dans {n} jours", "En {n} días"),

    # ---- 提示条（前端） ------------------------------------------------
    "toast.unstarred": ("已取消收藏", "已取消收藏", "Removed from starred",
                        "Retiré des favoris", "Quitado de favoritos"),
    "toast.error":    ("出错了", "出錯了", "Something went wrong",
                       "Une erreur est survenue", "Algo salió mal"),
    "toast.save_fail": ("保存失败", "儲存失敗", "Could not save",
                        "Échec de l'enregistrement", "No se pudo guardar"),
    "toast.starred":  ("已收藏·将于{date}提醒", "已收藏·將於{date}提醒",
                       "Starred · reminder {date}", "Ajouté · rappel {date}",
                       "Guardado · recordatorio {date}"),
    "toast.starred_no_date": ("已收藏·未设提醒", "已收藏·未設提醒", "Starred · no reminder",
                              "Ajouté · aucun rappel", "Guardado · sin recordatorio"),
    "toast.updated":  ("已更新·将于{date}提醒", "已更新·將於{date}提醒",
                       "Updated · reminder {date}", "Mis à jour · rappel {date}",
                       "Actualizado · recordatorio {date}"),
    "toast.updated_no_date": ("已更新·未设提醒", "已更新·未設提醒", "Updated · no reminder",
                              "Mis à jour · aucun rappel", "Actualizado · sin recordatorio"),
    "toast.checking": ("检查中…", "檢查中…", "Checking…", "Vérification…", "Comprobando…"),
    "toast.fetch_fail": ("抓取失败：", "抓取失敗：", "Check failed: ",
                         "Échec de la vérification : ", "Error al comprobar: "),
    "toast.result":   ("新增 {added} · 下架 {closed} · 在招 {total}",
                       "新增 {added} · 下架 {closed} · 在招 {total}",
                       "{added} new · {closed} delisted · {total} open",
                       "{added} nouvelles · {closed} retirées · {total} ouvertes",
                       "{added} nuevas · {closed} retiradas · {total} abiertas"),
    "toast.some_failed": ("（{n} 个来源抓取失败）", "（{n} 個來源抓取失敗）",
                          " ({n} sources failed)", " ({n} sources en échec)",
                          " ({n} fuentes fallaron)"),

    # ---- 来源名 --------------------------------------------------------
    "src.predoc":        ("predoc.org",) * 5,
    "src.nber":          ("NBER（本部）", "NBER（本部）", "NBER (internal)",
                          "NBER (interne)", "NBER (interno)"),
    "src.nber_external": ("NBER（非本部）", "NBER（非本部）", "NBER (external)",
                          "NBER (externe)", "NBER (externo)"),
})

WEEKDAYS = {
    "zh":      ("周一", "周二", "周三", "周四", "周五", "周六", "周日"),
    "zh-Hant": ("週一", "週二", "週三", "週四", "週五", "週六", "週日"),
    "en":      ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
    "fr":      ("Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"),
    "es":      ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"),
}

# 法语和西语的月份不首字母大写 —— 那是它们的正字法，不是笔误
MONTHS = {
    "en": ("January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"),
    "fr": ("janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"),
    "es": ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
           "agosto", "septiembre", "octubre", "noviembre", "diciembre"),
}

MONTHS_SHORT = {
    "en": ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"),
    "fr": ("janv.", "févr.", "mars", "avr.", "mai", "juin",
           "juil.", "août", "sept.", "oct.", "nov.", "déc."),
    "es": ("ene", "feb", "mar", "abr", "may", "jun",
           "jul", "ago", "sep", "oct", "nov", "dic"),
}


def normalise(lang):
    return lang if lang in LANGS else DEFAULT_LANG


def _idx(lang):
    return LANGS.index(normalise(lang))


def t(key, lang=DEFAULT_LANG, **kw):
    """取一条文案。

    西文串里用 | 分隔单数|复数，按传进来的 n 选一边；中文侧从不写 |。
    """
    row = S.get(key)
    if row is None:
        return key                              # 缺翻译时把键名露出来，便于发现
    text = row[_idx(lang)]
    if "|" in text:
        one, many = text.split("|", 1)
        text = one if kw.get("n") == 1 else many
    return text.format(**kw) if kw else text


def fdate(value, lang=DEFAULT_LANG):
    """卡片和徽章上的短日期。中文「09月06日」，英文「Sep 06」，法/西「6 sept.」。"""
    if not value:
        return ""
    try:
        d = datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except ValueError:
        return str(value)
    lang = normalise(lang)
    if lang in ("zh", "zh-Hant"):
        return d.strftime("%m月%d日")
    mon = MONTHS_SHORT[lang][d.month - 1]
    if lang == "en":
        return "%s %02d" % (mon, d.day)
    return "%d %s" % (d.day, mon)               # 法语西语是「日 月」的顺序


def weekdays(lang=DEFAULT_LANG):
    return WEEKDAYS[normalise(lang)]


def month_name(month, lang=DEFAULT_LANG):
    lang = normalise(lang)
    return str(month) if lang in ("zh", "zh-Hant") else MONTHS[lang][month - 1]


def source_label(source_id, lang=DEFAULT_LANG):
    return t("src." + source_id, lang)


def js_strings(lang):
    """前端要用到的那部分，注入页面供 app.js 取用。"""
    i = _idx(lang)
    return {k: v[i] for k, v in S.items() if k.startswith(("modal.", "toast."))}


def lang_options(current):
    """给选单用：[(代码, 母语名, 是否为当前), ...]"""
    cur = normalise(current)
    return [(code, LANG_NAMES[code], code == cur) for code in LANGS]


# 自检：任何一条少写一列都会在导入时立刻炸掉，不会悄悄漏翻
_bad = {k: len(v) for k, v in S.items() if len(v) != len(LANGS)}
if _bad:
    raise AssertionError("这些条目的语言数不对（应为 %d 列）：%s" % (len(LANGS), _bad))
