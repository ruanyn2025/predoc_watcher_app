'use strict';

/* 界面文案由服务端按当前语言注入到 window.S（见 i18n.py 的 js_strings）。
   模板里的静态文字已经翻好了，这里只管动态生成的那部分。 */
function S(key, vars) {
  let text = (window.STRINGS || {})[key] || key;
  if (vars) for (const k in vars) text = text.replaceAll('{' + k + '}', vars[k]);
  return text;
}

function toggleLangMenu(e) {
  e.stopPropagation();                       // 否则会立刻被下面那个"点别处就关"接住
  const m = document.getElementById('langMenu');
  m.hidden = !m.hidden;
  e.currentTarget.setAttribute('aria-expanded', String(!m.hidden));
}

function closeLangMenu() {
  const m = document.getElementById('langMenu');
  if (m && !m.hidden) {
    m.hidden = true;
    document.querySelector('.globe').setAttribute('aria-expanded', 'false');
  }
}

async function pickLang(code) {
  if (code === window.LANG) { closeLangMenu(); return; }
  await post('/api/lang', { lang: code });
  location.reload();
}

document.addEventListener('click', closeLangMenu);

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove('show'), 2200);
}

async function post(url, payload) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload || {}),
  });
  return r.json();
}

function ymd(d) {
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0')
       + '-' + String(d.getDate()).padStart(2, '0');
}

/* ---------------- 收藏 ---------------- */

let pendingKey = null;
let editing = false;         // true = 这条已经收藏过，面板是在改而不是在建

/* ☆ 收藏 / ★ 取消收藏。已收藏的卡片另有一个「编辑」按钮走 openEdit()。 */
async function toggleStar(btn) {
  const key = btn.dataset.key;
  if (btn.classList.contains('on')) {
    const r = await post('/api/unstar', { key });
    if (!r.ok) { toast(r.error || S('toast.error')); return; }
    btn.classList.remove('on');
    btn.textContent = '☆';
    const ed = btn.parentElement.querySelector('.edit');
    if (ed) ed.remove();
    toast(S('toast.unstarred'));
    if (/\/starred|\/calendar/.test(location.pathname)) {
      setTimeout(() => location.reload(), 700);
    }
    return;
  }
  openPanel(btn);
}

/* 收藏夹里那个显式的「编辑」按钮 */
function openEdit(btn) {
  openPanel(btn);
}

async function openPanel(btn) {
  const key = btn.dataset.key;
  pendingKey = key;
  const s = await post('/api/suggest', { key });
  if (!s.ok) { toast(s.error || S('toast.error')); return; }
  editing = !!s.starred;

  // 面板有两种形态：新收藏 vs 编辑已有的
  document.getElementById('smHeading').textContent =
    S(editing ? 'modal.edit_title' : 'modal.title');
  document.getElementById('smConfirm').textContent =
    S(editing ? 'modal.save' : 'modal.confirm');
  document.getElementById('smUnstar').hidden = !editing;

  document.getElementById('smTitle').textContent = btn.dataset.title || '';
  // 抽出日期就显示日期；抽不出但原文有话（Rolling 之类）就照搬原文；两者都无才是暂无
  document.getElementById('smDeadline').textContent =
    S('modal.deadline') + (s.parsed || s.deadline_raw || S('modal.none'));
  document.getElementById('smDate').value = s.remind_on;
  document.getElementById('smNote').value = s.note || '';   // 编辑时带出原备注
  document.getElementById('smDate').dataset.basis = s.basis;

  // 快捷按钮：解析出日期时给"提前几天"，否则给几个常用间隔
  const quick = document.getElementById('smQuick');
  quick.innerHTML = '';
  const add = (label, dateStr) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.textContent = label;
    b.onclick = () => { document.getElementById('smDate').value = dateStr; };
    quick.appendChild(b);
  };
  if (s.parsed) {
    const p = new Date(s.parsed + 'T00:00:00');
    [3, 7].forEach((n) => {
      const d = new Date(p); d.setDate(d.getDate() - n);
      if (d > new Date()) add(S('modal.before_n', { n }), ymd(d));
    });
    add(S('modal.on_deadline'), s.parsed);
  }
  [3, 7, 14, 30].forEach((n) => {
    const d = new Date(); d.setDate(d.getDate() + n);
    add(S('modal.in_n', { n }), ymd(d));
  });

  document.getElementById('starModal').hidden = false;
  document.getElementById('smDate').focus();
}

function closeStar() {
  document.getElementById('starModal').hidden = true;
  pendingKey = null;
  editing = false;
}

async function unstarFromModal() {
  if (!pendingKey) return;
  const key = pendingKey;
  const r = await post('/api/unstar', { key });
  if (!r.ok) { toast(r.error || S('toast.error')); return; }
  const btn = document.querySelector('.star[data-key="' + CSS.escape(key) + '"]');
  if (btn) {
    btn.classList.remove('on');
    btn.textContent = '☆';
    const ed = btn.parentElement.querySelector('.edit');
    if (ed) ed.remove();
  }
  closeStar();
  toast(S('toast.unstarred'));
  if (/\/starred|\/calendar/.test(location.pathname)) {
    setTimeout(() => location.reload(), 700);
  }
}

async function confirmStar() {
  if (!pendingKey) return;
  const dateEl = document.getElementById('smDate');
  const r = await post('/api/star', {
    key: pendingKey,
    remind_on: dateEl.value,
    basis: dateEl.dataset.basis || 'manual',
    note: document.getElementById('smNote').value,
  });
  if (!r.ok) { toast(r.error || S('toast.save_fail')); return; }

  const btn = document.querySelector('.star[data-key="' + CSS.escape(pendingKey) + '"]');
  if (btn) { btn.classList.add('on'); btn.textContent = '★'; }
  const wasEditing = editing;
  closeStar();
  const key = wasEditing ? 'toast.updated' : 'toast.starred';
  toast(dateEl.value ? S(key, { date: dateEl.value })
                     : S(wasEditing ? 'toast.updated_no_date' : 'toast.starred_no_date'));
  // 收藏夹和日历按提醒日期排版，改完得重排
  if (wasEditing && /\/starred|\/calendar/.test(location.pathname)) {
    setTimeout(() => location.reload(), 700);
  }
}

/* ---------------- 其他动作 ---------------- */

async function markRead(btn) {
  btn.disabled = true;
  const r = await post('/api/mark-read', {});
  if (r.ok) location.reload(); else { toast(S('toast.error')); btn.disabled = false; }
}

async function refreshData(btn) {
  btn.disabled = true;
  const old = btn.textContent;
  btn.textContent = S('toast.checking');
  const r = await post('/api/refresh', {});
  btn.disabled = false;
  btn.textContent = old;
  if (!r.ok) { toast(S('toast.fetch_fail') + r.error); return; }
  const d = r.result;
  const failed = Object.keys(d.failures || {}).length;
  toast(S('toast.result', { added: d.added, closed: d.closed, total: d.total })
        + (failed ? S('toast.some_failed', { n: failed }) : ''));
  if (d.added || d.closed) setTimeout(() => location.reload(), 1200);
}

/* ---------------- 键盘 ---------------- */

document.addEventListener('keydown', (e) => {
  const open = !document.getElementById('starModal').hidden;
  if (e.key === 'Escape' && open) closeStar();
  if (e.key === 'Enter' && open && e.target.tagName !== 'BUTTON') confirmStar();
});

document.getElementById('starModal').addEventListener('click', (e) => {
  if (e.target.id === 'starModal') closeStar();
});
