'use strict';

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

async function toggleStar(btn) {
  const key = btn.dataset.key;
  if (btn.classList.contains('on')) {
    const r = await post('/api/unstar', { key });
    if (r.ok) { btn.classList.remove('on'); btn.textContent = '☆'; toast('已取消收藏'); }
    return;
  }
  pendingKey = key;
  const s = await post('/api/suggest', { key });
  if (!s.ok) { toast(s.error || '出错了'); return; }

  document.getElementById('smTitle').textContent = btn.dataset.title || '';
  document.getElementById('smRaw').textContent = s.deadline_raw || '（该来源没有截止日期字段）';
  document.getElementById('smLabel').textContent = s.label
    + (s.basis === 'deadline' ? ' → 采用这个日期' : ' → 预填为 7 天后');
  document.getElementById('smDate').value = s.remind_on;
  document.getElementById('smNote').value = '';
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
    [[3, '提前 3 天'], [7, '提前 7 天']].forEach(([n, lab]) => {
      const d = new Date(p); d.setDate(d.getDate() - n);
      if (d > new Date()) add(lab, ymd(d));
    });
    add('就在截止日', s.parsed);
  }
  [[3, '3 天后'], [7, '7 天后'], [14, '14 天后'], [30, '30 天后']].forEach(([n, lab]) => {
    const d = new Date(); d.setDate(d.getDate() + n);
    add(lab, ymd(d));
  });

  document.getElementById('starModal').hidden = false;
  document.getElementById('smDate').focus();
}

function closeStar() {
  document.getElementById('starModal').hidden = true;
  pendingKey = null;
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
  if (!r.ok) { toast(r.error || '保存失败'); return; }

  const btn = document.querySelector('.star[data-key="' + CSS.escape(pendingKey) + '"]');
  if (btn) { btn.classList.add('on'); btn.textContent = '★'; }
  closeStar();
  toast('已收藏，' + (dateEl.value ? dateEl.value + ' 提醒你' : '未设提醒'));
}

/* ---------------- 其他动作 ---------------- */

async function markRead(btn) {
  btn.disabled = true;
  const r = await post('/api/mark-read', {});
  if (r.ok) location.reload(); else { toast('出错了'); btn.disabled = false; }
}

async function refreshData(btn) {
  btn.disabled = true;
  const old = btn.textContent;
  btn.textContent = '同步中…';
  const r = await post('/api/refresh', {});
  btn.disabled = false;
  btn.textContent = old;
  if (!r.ok) { toast('同步失败：' + r.error); return; }
  const d = r.result;
  toast('新增 ' + d.added + ' · 下架 ' + d.closed + ' · 在库 ' + d.total);
  if (d.added || d.closed) setTimeout(() => location.reload(), 900);
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
