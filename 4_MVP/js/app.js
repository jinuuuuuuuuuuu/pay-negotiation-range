// 화면 로직. 계산은 모두 engine.js(formula.py와 일치 테스트로 묶음)가 하고, 여기서는 보여 주기만 한다.
import * as E from './engine.js';
import { icon } from './icons.js';

const $view = document.getElementById('view');
const $top = document.getElementById('topbar');
const $tabs = document.getElementById('tabbar');
let CTX = null;
let PEERS_RAW = null;
let LAST_FIRM = null;
const STATE = new Map();              // 회사별 입력값 (노조안·회사안, 가정, 이익연동, 불황 점검 설정)

// ---------------------------------------------------------------- 형식
const isNum = (v) => typeof v === 'number' && Number.isFinite(v);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const minus = (v) => (v < 0 ? '−' : '');
const pct = (v, d = 1) => (isNum(v) ? `${minus(v)}${Math.abs(v * 100).toFixed(d)}%` : '—');
const pctRaw = (v, d = 1) => (isNum(v) ? `${minus(v)}${Math.abs(v).toFixed(d)}%` : '—');
const signed = (v, d = 1, unit = '%') => (isNum(v) ? `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(d)}${unit}` : '—');
function won(x) {
  if (!isNum(x)) return '—';
  const a = Math.abs(x), s = minus(x);
  if (a >= 1e12) return `${s}${(a / 1e12).toFixed(2).replace(/\.?0+$/, '')}조\u00A0원`;
  if (a >= 1e8) return `${s}${Math.round(a / 1e8).toLocaleString('ko-KR')}억\u00A0원`;
  if (a >= 1e4) return `${s}${Math.round(a / 1e4).toLocaleString('ko-KR')}만 원`;
  return `${s}${Math.round(a).toLocaleString('ko-KR')}원`;
}
const man = (x) => (isNum(x) ? `${Math.round(x / 1e4).toLocaleString('ko-KR')}만 원` : '—');
const man0 = (x) => (isNum(x) ? `${Math.round(x / 1e4).toLocaleString('ko-KR')}만` : '—');
// formula.py가 만든 문구의 '업종'을 화면에서는 '업계'로 (계산·결과 파일은 그대로)
const u = (s) => String(s ?? '').replace(/업종/g, '업계');
// 불황 이름의 근거 수준 꼬리표는 화면에서만 뗀다 (계산 키는 그대로)
const RANGE_MSG = {
  '업계 수준 이상도 업계만큼의 부담으로 감당 가능': '업계보다 더 올려도 부담은 업계 수준입니다',
  '업계만큼 주면 우리 부담이 업계보다 큼. 이익연동 전환 검토': '업계만큼 올리면 부담이 업계보다 커서, 이익 기준 성과급을 함께 검토해 보세요',
  '하한(업계 인상률)만 제시. 고정 인상보다 이익연동 전환을 함께 검토': '하한(업계 인상률)만 제시합니다. 고정 인상보다 이익 기준 성과급을 함께 검토해 보세요',
};
const shortScn = (x) => scnLabel(x).replace(/\([^)]*\)\s*(?=\(\d{4}\))/, ' ').replace(' · 우리 업계 최악의 해', ' · 최악의 해').replace(/\s{2,}/g, ' ');
const scnLabel = (s) => u(s).replace(/\s*\((일부 근거|원인 미확인)\)/g, '');

const CAP_LABEL = {
  '여력 있음': '업계보다 높음',
  '여력 보통': '업계보다 낮음',
  '여력 제약': '제약',
  '판정 불가': '판정 불가',
};
function posClass(p) {
  if (!p) return 'hold';
  if (p.startsWith('구간 안')) return 'inside';
  if (p === '하한 미달' || p === '상한 이하') return 'below';
  if (p === '상한 초과' || p === '하한 이상·상한 초과') return 'above';
  return 'hold';
}
// 업계 불황 대비 점검의 행 이름·종류를 쉬운 말로
const SCN_NAME = { 평상시: '불황 미발생', '모델 중앙(P50)': '모델 예측: 보통 시나리오', '모델 나쁜 쪽(P10)': '모델 예측: 최악의 시나리오' };
const scnName = (n) => u(SCN_NAME[n] || n);
const SCN_KIND = { 평상시: '기본', '공통 사건': '모든 업계 공통', '우리 업종 사건': '우리 업계 사건', '최악의 해': '우리 업계 최악의 해', '직접 입력': '직접 입력' };

// ---------------------------------------------------------------- 상태
function st(id) {
  if (!STATE.has(id)) {
    const f = CTX.firms.get(id);
    const lo = isNum(f.peer_growth) ? f.peer_growth : 0.04;
    const r05 = (v) => Math.max(0, Math.round(v * 200) / 200);
    STATE.set(id, {
      union: { base: r05(lo + 0.02), bonus: 0 },
      company: { base: r05(lo - 0.01), bonus: 0.01 },
      override: null, headcount: 0, sales: 0,
      link: { mode: 'rate', rate: CTX.C.PAY_RATE, amount: null, demand: 0.10 },
      risk: { severity: '중앙', withSales: true, pick: null, dm: -0.03, dr: -0.10 },
    });
  }
  return STATE.get(id);
}

// ---------------------------------------------------------------- 데이터
async function loadAll() {
  const names = ['meta', 'firms', 'peers', 'forecast', 'shocks', 'catalog'];
  const got = await Promise.all(names.map(async (n) => {
    const r = await fetch(`data/${n}.json`);
    if (!r.ok) throw new Error(`${n}.json (${r.status})`);
    return r.json();
  }));
  const d = Object.fromEntries(names.map((n, i) => [n, got[i]]));
  CTX = E.buildContext(d);
  PEERS_RAW = d.peers;
  CTX.list = [...CTX.firms.values()].map((f) => ({
    id: f.id, name: f.name, key: (f.name || '').replace(/\s+/g, '').toLowerCase(),
    code: f.stock_code || '', ind: f.ind2_name || '', size: isNum(f.S_T) ? f.S_T : 0,
  }));
}
function peersOf(id) {
  const ids = PEERS_RAW ? PEERS_RAW[id] || [] : [];
  return ids.map((p) => CTX.firms.get(p)).filter(Boolean);
}

// ---------------------------------------------------------------- 틀
function setTop({ title = '', back = null, dark = false, about = true } = {}) {
  $top.className = `topbar${dark ? ' on-dark' : ''}`;
  $view.classList.toggle('dark-top', dark);
  $top.innerHTML = `
    ${back ? `<a class="icon-btn" href="${back}" aria-label="뒤로">${icon('chevron-left', 24)}</a>` : '<span class="spacer"></span>'}
    <h1>${esc(title)}</h1>
    ${about ? `<a class="icon-btn" href="#/about" aria-label="계산 근거">${icon('info', 22)}</a>` : '<span class="spacer"></span>'}`;
  document.querySelector('meta[name="theme-color"]').content = dark ? '#1F1F1F' : '#F3F3F2';
}
function setTabs(id, active) {
  if (!id) { $tabs.hidden = true; $view.classList.add('no-tabs'); return; }
  $tabs.hidden = false; $view.classList.remove('no-tabs');
  const t = [['', '요약', 'house'], ['/range', '협상 구간', 'scale'], ['/link', '기준 환산', 'coins'], ['/risk', '미래 위험', 'cloud-lightning']];
  $tabs.innerHTML = t.map(([p, l, ic]) => `<a class="tab" href="#/f/${id}${p}" ${active === p ? 'aria-current="page"' : ''}>${icon(ic, 22)}<span>${l}</span></a>`).join('');
}

// ---------------------------------------------------------------- 그래프 공통
const W = 340;
const tx = (x, y, t, cls = 'cl', anchor = 'start') => `<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" class="${cls}" text-anchor="${anchor}">${esc(t)}</text>`;
function niceMax(v) {
  if (!(v > 0)) return 1;
  const p = 10 ** Math.floor(Math.log10(v));
  for (const m of [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (v <= m * p) return m * p;
  return 10 * p;
}
const clamp = (v, a, b) => Math.min(Math.max(v, a), b);

// 업계 대비 임금 위치: x = 회사(1인당 급여 낮은 순 → 높은 순), y = 1인당 급여
// 배경 음영 = 판정 기준 자리. P(우리보다 낮은 비교 회사 비율) ≤ 0.25면 임금 낮음, ≥ 0.75면 임금 높음(formula.py HIGH_P·LOW_P).
// 오름차순에서 i번째 칸에 서면 P = i ÷ 비교 회사 수이므로, 왼쪽·오른쪽 음영 칸이 곧 판정 구간이다.
const LOW_P = 0.25, HIGH_P = 0.75;
function wageChart(f) {
  const peers = peersOf(f.id).filter((p) => isNum(p.w));
  if (!peers.length || !isNum(f.w)) return { svg: '<p class="note">비교할 업계 회사가 없어 그래프를 그릴 수 없습니다.</p>', rank: null, n: 0, items: [] };
  const items = [...peers.map((p) => ({ w: p.w, name: p.name, us: false })), { w: f.w, name: f.name, us: true }].sort((a, b) => a.w - b.w);
  const n = items.length, k = n - 1, ui = items.findIndex((x) => x.us), rank = n - ui;  // rank: 높은 순 순위
  const H = 236, T = 48, B = 40, L = 2, R = 2, ph = H - T - B, base = T + ph;
  const max = niceMax(items[n - 1].w * 1.04);
  const step = (W - L - R) / n, bw = clamp(step * 0.42, 5, 9);  // 키트 막대: 가늘고 끝이 둥근 기둥
  const sx = (i) => L + i * step;
  const py = (v) => T + ph * (1 - v / max);
  const med = isNum(f.peer_median_10k) ? f.peer_median_10k * 1e4 : NaN;

  // 판정 구간 음영 (하위 25% / 상위 25%)
  const loEnd = Math.floor(LOW_P * k) + 1, hiStart = Math.ceil(HIGH_P * k);
  const zone = (a, b, lab, anchor) => `<rect x="${sx(a).toFixed(1)}" y="${T - 20}" width="${(sx(b) - sx(a)).toFixed(1)}" height="${(base - T + 20).toFixed(1)}" class="zone-q"/>`
    + tx(anchor === 'start' ? sx(a) + 5 : sx(b) - 5, T - 7, lab, 'cl-z', anchor);
  const zones = zone(0, loEnd, '하위 25%', 'start') + zone(hiStart, n, '상위 25%', 'end');

  let bars = '', hits = '';
  // 우리 회사 칸 강조 띠 (그래프 위 끝 ~ 축)
  const usLate = `style="--d:${Math.round(ui * Math.min(22, 440 / n)) + 380}ms"`;
  const usBand = `<rect x="${(sx(ui) + 1).toFixed(1)}" y="${T - 2}" width="${(step - 2).toFixed(1)}" height="${(base - T + 2).toFixed(1)}" rx="${((step - 2) / 2).toFixed(1)}" class="col-us" ${usLate}/>`;
  // 등장 움직임: 막대가 왼쪽부터 차례로 자람(전체 지연 최대 440ms). 우리 배지는 우리 막대가 다 자랄 때.
  const lag = Math.min(22, 440 / n);
  items.forEach((it, i) => {
    const w = it.us ? bw + 2 : bw, x = sx(i) + (step - w) / 2, y = py(it.w);
    bars += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${w.toFixed(1)}" height="${(base - y).toFixed(1)}" rx="${(w / 2).toFixed(1)}" class="${it.us ? 'bar-us' : 'bar'}" data-i="${i}" style="--d:${Math.round(i * lag)}ms"/>`;
    hits += `<rect x="${sx(i).toFixed(1)}" y="${T - 20}" width="${step.toFixed(1)}" height="${(base - T + 20).toFixed(1)}" class="hit" data-i="${i}"/>`;
  });

  let medEl = '';
  if (isNum(med)) {
    const my = py(med);
    medEl = `<line x1="${L}" x2="${W - R}" y1="${my.toFixed(1)}" y2="${my.toFixed(1)}" class="ln-ind"/>`
      + `<text x="${(L + 4).toFixed(1)}" y="${(my - 6).toFixed(1)}" class="cl-m halo" text-anchor="start">${esc(`업계 중앙 ${man0(med)}`)}</text>`;
  }
  // 우리 막대 위 먹색 알약 이름표 (키트·참고 이미지의 값 배지)
  const ux = sx(ui) + step / 2, uy = py(f.w);
  const labText = `우리 ${man0(f.w)}`;
  const pw = 18 + [...labText].reduce((s, c) => s + (/[가-힣]/.test(c) ? 13 : c === ' ' ? 3.4 : 7.4), 0), ph2 = 22;
  const px = clamp(ux - pw / 2, L, W - R - pw);
  let pyTop = uy - ph2 - 6;
  // 중앙선 라벨(왼쪽 위, 폭 약 100)과 겹치면 한 줄 위로
  if (isNum(med) && px < L + 108 && pyTop + ph2 > py(med) - 18 && pyTop < py(med) + 2) pyTop = py(med) - 20 - ph2;
  pyTop = Math.max(pyTop, T - 32);
  const lab = `<g class="pill-us" ${usLate}><rect x="${px.toFixed(1)}" y="${pyTop.toFixed(1)}" width="${pw.toFixed(1)}" height="${ph2}" rx="${ph2 / 2}"/>`
    + `<text x="${(px + pw / 2).toFixed(1)}" y="${(pyTop + 15.5).toFixed(1)}" text-anchor="middle">${esc(labText)}</text></g>`;

  // 양 끝 값(우리 막대가 끝에 있으면 위 라벨과 겹치므로 생략)
  const ends = (ui === 0 ? '' : tx(sx(0), base + 17, man0(items[0].w), 'cl'))
    + (ui === n - 1 ? '' : tx(sx(n), base + 17, man0(items[n - 1].w), 'cl', 'end'));
  const axis = `<line x1="${L}" x2="${W - R}" y1="${base}" y2="${base}" class="ax"/>${ends}${tx(W / 2, H - 4, '← 급여 낮음 · 높음 →', 'cl', 'middle')}`;
  return {
    svg: `<div class="chart-wrap" data-wage>
      <svg class="chart wage" viewBox="0 0 ${W} ${H}" tabindex="0" role="img" aria-label="비교군 ${k}곳과 우리 회사의 1인당 급여, 낮은 순에서 높은 순. 우리 회사 ${n}곳 중 ${rank}위. 막대를 누르면 회사 이름이 나옵니다. 화살표 키로 옮길 수 있습니다.">${zones}${usBand}${medEl}${bars}${axis}${lab}${hits}</svg>
      <div class="chart-tip" role="status" aria-live="polite" hidden></div>
    </div>`,
    rank, n, items,
  };
}

// ---------------------------------------------------------------- 움직임 공통
// morph: 다시 그릴 때 통째로 바꾸지 않고 바뀐 곳만 고친다. 그래프 좌표는 미끄러지고(tween),
// 바뀐 숫자 칸은 잠깐 노랗게 빛나고(bump), 판정 배지는 톡 튄다. 모양이 달라지면 통째로 바꾸고 살짝 떠오르게.
const NUM_ATTR = new Set(['x', 'y', 'cx', 'cy', 'r', 'x1', 'x2', 'y1', 'y2', 'width', 'height', 'rx']);
const ownTexts = (el) => [...el.childNodes].filter((n) => n.nodeType === 3);
const shapeOf = (root) => [ownTexts(root).length, ...[...root.querySelectorAll('*')].map((e) => `${e.tagName}${ownTexts(e).length}`)].join('|');
function morph(box, html) {
  const tpl = document.createElement('template');
  tpl.innerHTML = html;
  const nw = tpl.content;
  // 모양이 다르면 그대로 바꿔 끼운다(흐려짐 효과 없음 — 입력 중 깜빡임 방지)
  if (!box.firstElementChild || shapeOf(box) !== shapeOf(nw)) { box.replaceChildren(nw); return; }
  const oldEls = [...box.querySelectorAll('*')], newEls = [...nw.querySelectorAll('*')];
  const syncText = (o, n) => {
    const a = ownTexts(o), b = ownTexts(n);
    let changed = false;
    a.forEach((t, i) => { if (t.nodeValue !== b[i].nodeValue) { t.nodeValue = b[i].nodeValue; if (b[i].nodeValue.trim()) changed = true; } });
    return changed;
  };
  syncText(box, nw);
  const tw = [];
  oldEls.forEach((o, i) => {
    const n = newEls[i], svg = o instanceof SVGElement;
    let clsChanged = false;
    for (const a of [...o.attributes]) if (!n.hasAttribute(a.name)) o.removeAttribute(a.name);
    for (const a of [...n.attributes]) {
      const ov = o.getAttribute(a.name);
      if (ov === a.value) continue;
      if (svg && NUM_ATTR.has(a.name) && ov !== null && Number.isFinite(+ov) && Number.isFinite(+a.value)) tw.push([o, a.name, +ov, a.value]);
      else { o.setAttribute(a.name, a.value); if (a.name === 'class') clsChanged = true; }
    }
    syncText(o, n);
    if (!svg && clsChanged && o.classList.contains('badge')) pop(o);   // 판정이 바뀔 때만 톡 (숫자 반짝임은 없앰)
  });
  if (tw.length) tween(tw, 300);
}
function tween(list, ms) {
  if (REDUCED()) { list.forEach(([el, a, , to]) => el.setAttribute(a, to)); return; }
  const t0 = performance.now(), ease = (t) => 1 - (1 - t) ** 3;
  list.forEach(([el, a]) => { (el._tw ||= {})[a] = t0; });
  const step = (now) => {
    const t = Math.min((now - t0) / ms, 1), k = ease(t);
    list.forEach(([el, a, from, to]) => { if (el._tw[a] === t0) el.setAttribute(a, t === 1 ? to : (from + (+to - from) * k).toFixed(2)); });
    if (t < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
function pop(el) {
  if (REDUCED() || el._popAt > performance.now() - 400) return;
  el._popAt = performance.now();
  el.animate([{ transform: 'scale(0.82)' }, { transform: 'scale(1.06)', offset: 0.55 }, { transform: 'scale(1)' }], { duration: 320, easing: 'cubic-bezier(0.16, 1, 0.3, 1)' });
}
// 처음 그릴 때만 등장 움직임 클래스(enter)를 붙였다가 뗀다 → 이후 다시 그려도 재생되지 않음
function enterOnce(box, cls = 'enter', ms = 1500) {
  if (box.dataset.entered) return;
  box.dataset.entered = '1';
  box.classList.add(cls);
  setTimeout(() => box.classList.remove(cls), ms);
}

// 등장 움직임: 그래프가 화면에 들어올 때 한 번. 기본 상태는 '보이는 상태'라 스크립트가 실패해도 화면이 비지 않는다.
const REDUCED = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches;
// 나가는 움직임(Ease in): .is-out으로 사라지는 애니메이션을 재생한 뒤 hidden. 다시 보이면 취소.
function fadeHide(el, ms = 200) {
  if (!el || el.hidden) return;
  if (REDUCED()) { el.hidden = true; return; }
  el.classList.add('is-out');
  clearTimeout(el._outT);
  el._outT = setTimeout(() => { if (el.classList.contains('is-out')) { el.hidden = true; el.classList.remove('is-out'); } }, ms);
}
function fadeShow(el) {
  if (!el) return;
  clearTimeout(el._outT);
  el.classList.remove('is-out');
  el.hidden = false;
}
function playWageEntrance(wrap, onPlayed = () => {}) {
  if (REDUCED() || !('IntersectionObserver' in window)) return;
  const svg = wrap.querySelector('svg');
  const num = wrap.closest('.panel')?.querySelector('.big-num[data-count]');
  svg.classList.add('pre');                       // 막대 0 높이에서 대기 (인쇄 때는 CSS가 끝 상태로)
  const io = new IntersectionObserver((ents) => {
    if (!ents.some((e) => e.isIntersecting)) return;
    io.disconnect();
    void svg.getBoundingClientRect();             // 대기 상태를 한 번 그린 뒤 시작
    requestAnimationFrame(() => { svg.classList.remove('pre'); svg.classList.add('play'); });
    if (num) countUp(num, Number(num.dataset.count), 400);
    setTimeout(onPlayed, 1300);
  }, { threshold: 0.35 });
  io.observe(svg);
}
function countUp(el, to, ms, fmt = (v) => Math.round(v).toLocaleString('ko-KR')) {
  if (REDUCED()) return;
  const t0 = performance.now(), ease = (t) => 1 - (1 - t) ** 4;
  const tick = (now) => {
    const t = Math.min((now - t0) / ms, 1);
    el.textContent = fmt(to * ease(t));
    if (t < 1 && el.isConnected) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

// 임금 막대 탭·호버·화살표 키 → 회사명과 급여
function bindWageChart(root, items) {
  const wrap = root.querySelector('[data-wage]');
  if (!wrap || !items.length) return;
  const svg = wrap.querySelector('svg'), tip = wrap.querySelector('.chart-tip');
  const bars = [...svg.querySelectorAll('rect[class^="bar"]')];
  let cur = -1;
  let touched = false;
  const show = (i, hint = false) => {
    if (i < 0 || i >= items.length) return;
    cur = i;
    bars.forEach((b) => b.classList.toggle('sel', Number(b.dataset.i) === i));
    const it = items[i], r = items.length - i;
    tip.innerHTML = `<strong>${esc(it.us ? `${it.name} (우리)` : it.name)}</strong><span class="num">${man(it.w)} · ${r}위</span>${hint ? '<span class="hint">다른 막대도 눌러 보세요</span>' : ''}`;
    fadeShow(tip);
    const box = svg.getBoundingClientRect(), bar = bars[i].getBoundingClientRect();
    const cx = bar.left + bar.width / 2 - box.left;
    const tw = tip.offsetWidth;
    tip.style.left = `${clamp(cx - tw / 2, 0, box.width - tw)}px`;
    tip.style.top = `${Math.max(bar.top - box.top - tip.offsetHeight - 8, 0)}px`;
  };
  const hide = () => { cur = -1; fadeHide(tip); bars.forEach((b) => b.classList.remove('sel')); };
  // 등장이 끝나면 우리 막대에 툴팁을 한 번 띄워 '누르면 회사명이 나온다'를 알려 준다 (손대면 바로 사라짐)
  playWageEntrance(wrap, () => {
    if (touched || !svg.isConnected) return;
    show(items.findIndex((x) => x.us), true);
    setTimeout(() => { if (!touched && svg.isConnected) hide(); }, 2600);
  });
  const at = (e) => { const t = e.target.closest('[data-i]'); return t ? Number(t.dataset.i) : -1; };
  svg.addEventListener('pointerdown', (e) => { touched = true; const i = at(e); if (i >= 0) { if (i === cur && e.pointerType !== 'mouse') hide(); else show(i); } });
  svg.addEventListener('pointermove', (e) => { if (e.pointerType === 'mouse') { const i = at(e); if (i >= 0 && i !== cur) show(i); } });
  svg.addEventListener('pointerleave', (e) => { if (e.pointerType === 'mouse') hide(); });
  svg.addEventListener('keydown', (e) => {
    touched = true;
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      const start = cur < 0 ? items.findIndex((x) => x.us) : cur;
      show(clamp(start + (e.key === 'ArrowRight' ? 1 : -1), 0, items.length - 1));
    } else if (e.key === 'Escape') hide();
  });
  svg.addEventListener('blur', hide);
}

// 임금 위치 머리: 결론 문장 + 순위 배지 + 보조 줄
function wageHead(f, wc) {
  if (!wc.rank) return '';
  const d = isNum(f.wage_10k) && isNum(f.peer_median_10k) ? Math.round(f.wage_10k - f.peer_median_10k) : NaN;
  // 키트 그래프 카드 머리: 작은 라벨 + 큰 숫자 + 작은 단위
  const claim = !isNum(d) ? '<span class="big-unit">업계 중앙과 비교할 수 없음</span>'
    : d === 0 ? '<span class="big-num">같음</span>'
      : `<span class="big-num" data-count="${Math.abs(d)}">${Math.abs(d).toLocaleString('ko-KR')}</span><span class="big-unit">만 원 ${d > 0 ? '높음' : '낮음'}</span>`;
  const share = wc.rank / wc.n;
  const top = share <= 0.5 ? `상위 ${Math.max(1, Math.round(share * 100))}%` : `하위 ${Math.max(1, Math.round((wc.n - wc.rank + 1) / wc.n * 100))}%`;
  const warn = f.peer_warn
    ? `<button type="button" class="tip-btn" aria-expanded="false" aria-controls="wage-warn" aria-label="비교군 주의 보기">${icon('info', 18)}</button>` : '';
  return `<div class="wage-head">
      <div class="card-top"><span class="cap">업계 중앙보다</span>${warn}</div>
      <p class="wage-claim num" aria-hidden="true">${claim}</p>
      <p class="sr-only">업계 중앙보다 ${isNum(d) ? (d === 0 ? '같음' : `${Math.abs(d).toLocaleString('ko-KR')}만 원 ${d > 0 ? '높음' : '낮음'}`) : '비교할 수 없음'}</p>
      ${f.peer_warn ? `<div class="wage-warn" id="wage-warn" hidden>${facts([['주의', esc(u(f.peer_warn))], ['기준', '비교군 매출 중앙값이 우리의 1/3 미만 또는 3배 초과']])}</div>` : ''}
      <p class="wage-meta"><span class="badge rank num">${wc.n}곳 중 ${wc.rank}위</span><span class="num">${top}</span></p>
    </div>`;
}

// 협상 구간: x = 기본급 인상률, y = 인상 비용 ÷ 영업이익(3년 평균 기준, 기본급 인상분)
// 협상 구간 눈금자: 기본급 인상률 한 줄을 3칸(업계보다 뒤처짐 / 협상 구간 / 업계보다 부담 큼)으로 칠하고,
// 경계 위에 하한·상한 알약(근거 한 줄), 아래에 노조안·회사안 핀. 값이 바뀌어도 요소 구성은 같게 유지(입력 중 깜빡임 방지).
function rangeChart(f, rng, offers = null, compact = false) {
  const showMax = CTX.C.RANGE_UPPER_SHOW_MAX;
  const g = rng['하한'], up = rng['상한'];
  if (!isNum(g)) return '';
  const hasUp = isNum(up), okRange = hasUp && up >= g, over = hasUp && up > showMax;
  const xc = [0.1, g * 1.5];
  if (hasUp && !over) xc.push(up * 1.25);
  if (offers) xc.push(offers.union * 1.15, offers.company * 1.15);
  const M = Math.min(Math.ceil(Math.max(...xc) * 100) / 100, 0.2);
  const L = 12, R = 12, bw = W - L - R;
  const px = (x) => L + (clamp(x, 0, M) / M) * bw;
  const top = 58, bh = 34, H = compact ? top + bh + 34 : top + bh + 92;
  const xg = px(g), xu = hasUp ? (over ? W - R : px(up)) : null;
  // 칸 3개 (없는 칸은 너비 0으로 두어 모양을 유지)
  const z = [];
  if (okRange) z.push([L, xg, 'rz-lo', '업계보다 뒤처짐'], [xg, xu, 'rz-in', '협상 구간'], [xu, W - R, 'rz-hi', '업계보다 부담 큼']);
  else if (hasUp) z.push([L, xg, 'rz-lo', '업계보다 뒤처짐'], [xg, xg, 'rz-in', ''], [xg, W - R, 'rz-hi', '업계보다 부담 큼']);
  else z.push([L, xg, 'rz-lo', '업계보다 뒤처짐'], [xg, W - R, 'rz-in hold', '하한 이상'], [W - R, W - R, 'rz-hi', '']);
  let s = `<defs><clipPath id="rb${compact ? 'c' : 'f'}"><rect x="${L}" y="${top}" width="${bw}" height="${bh}" rx="10"/></clipPath></defs><g clip-path="url(#rb${compact ? 'c' : 'f'})">`;
  z.forEach(([a, b, cls]) => { s += `<rect x="${a.toFixed(1)}" y="${top}" width="${Math.max(b - a, 0).toFixed(1)}" height="${bh}" class="${cls}"/>`; });
  s += '</g>';
  z.forEach(([a, b, , lab]) => { const w = b - a; s += `<text x="${((a + b) / 2).toFixed(1)}" y="${top + bh / 2 + 4.5}" class="rz-t${w < tw0(lab) + 10 || !lab ? ' off' : ''}" text-anchor="middle">${esc(lab)}</text>`; });
  // 경계 표시선 + 알약(값) + 근거 한 줄
  const gLab = `하한 ${pct(g)}`, uLab = hasUp ? (over ? `상한 ${Math.round(showMax * 100)}% 초과` : `상한 ${pct(up)}`) : '';
  const wG = tw1(gLab), wU = hasUp ? tw1(uLab) : 0;
  let lG = clamp(xg - wG / 2, 2, W - 2 - wG), lU = hasUp ? clamp(xu - wU / 2, 2, W - 2 - wU) : 0;
  if (hasUp) {
    const gFirst = xg <= xu, [w1, w2] = gFirst ? [wG, wU] : [wU, wG];
    let l1 = gFirst ? lG : lU, l2 = gFirst ? lU : lG;
    if (l1 + w1 + 8 > l2) {
      const mid = (xg + xu) / 2;
      l1 = mid - (w1 + w2 + 8) / 2; l2 = l1 + w1 + 8;
      if (l1 < 2) { l2 += 2 - l1; l1 = 2; }
      if (l2 + w2 > W - 2) { l1 -= l2 + w2 - (W - 2); l2 = W - 2 - w2; }
    }
    if (gFirst) { lG = l1; lU = l2; } else { lU = l1; lG = l2; }
  }
  const mark = (x, l, w, lab, why, cls) => `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${top - 8}" y2="${top + bh}" class="rz-mk ${cls}"/>`
    + `<g class="rz-pill ${cls}"><rect x="${l.toFixed(1)}" y="2" width="${w.toFixed(1)}" height="24" rx="12"/><text x="${(l + w / 2).toFixed(1)}" y="18.5" text-anchor="middle">${esc(lab)}</text></g>`
    + `<text x="${(l + w / 2).toFixed(1)}" y="${top - 14}" class="rz-why" text-anchor="middle">${esc(why)}</text>`;
  s += mark(xg, lG, wG, gLab, '업계 인상률', 'lo');
  if (hasUp) s += mark(xu, lU, wU, uLab, '업계와 같은 부담', 'up');
  // 눈금
  const tickY = top + bh + 16;
  for (let v = 0; v <= M + 1e-9; v += 0.01) {
    const x = px(v), lab = Math.round(v * 100) % 5 === 0 || v === 0;
    s += `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${top + bh + 2}" y2="${top + bh + (lab ? 7 : 4)}" class="rz-tk"/>`;
    if (lab) s += tx(clamp(x, L + 6, W - R - 8), tickY, `${Math.round(v * 100)}%`, 'cl', v === 0 ? 'start' : 'middle');
  }
  // 노조안·회사안 핀 (가까우면 위아래로 엇갈림)
  if (offers && !compact) {
    const xU = px(offers.union), xC = px(offers.company), close = Math.abs(xU - xC) < 84;
    const pin = (x, who, v, row, cls) => {
      const lab = `${who} ${pct(v)}`, w = tw1(lab), y = top + bh + 30 + row * 30, l = clamp(x - w / 2, 2, W - 2 - w);
      return `<line x1="${x.toFixed(1)}" x2="${x.toFixed(1)}" y1="${top + bh}" y2="${y}" class="rz-pin ${cls}"/>`
        + `<circle cx="${x.toFixed(1)}" cy="${top + bh}" r="7" class="${cls === 'un' ? 'pt-un' : 'pt-co'}"/>`
        + `<g class="rz-chip ${cls}"><rect x="${l.toFixed(1)}" y="${y}" width="${w.toFixed(1)}" height="24" rx="12"/><text x="${(l + w / 2).toFixed(1)}" y="${y + 16.5}" text-anchor="middle">${esc(lab)}</text></g>`;
    };
    const unLow = close && xU < xC;   // 가까우면 왼쪽 핀을 아래 줄로
    s += pin(xC, '회사안', offers.company, close && !unLow ? 1 : 0, 'co');
    s += pin(xU, '노조안', offers.union, unLow ? 1 : 0, 'un');
  }
  const aria = `협상 구간 눈금자. 하한 ${pct(g)}(업계 인상률)${hasUp ? `, 상한 ${rng['상한 표시']}(업계와 같은 부담)` : ''}${offers ? `, 노조안 ${pct(offers.union)}, 회사안 ${pct(offers.company)}` : ''}`;
  const legend = `<ul class="legend-row rz-legend">
      <li><i class="sw rz-sw-lo"></i>업계보다 뒤처짐</li>
      <li><i class="sw rz-sw-in${hasUp ? '' : ' hold'}"></i>${hasUp ? '협상 구간' : '하한 이상'}</li>
      ${hasUp ? '<li><i class="sw rz-sw-hi"></i>업계보다 부담 큼</li>' : ''}
    </ul>`;
  return `<p class="chart-y">기본급 인상률</p><svg class="chart rz" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(aria)}">${s}</svg>`;
}
// 글자 폭 어림 (12.5px 굵게 알약 / 12px 칸 이름)
const tw1 = (t) => [...t].reduce((a, ch) => a + (/[가-힣]/.test(ch) ? 12.5 : ch === ' ' || ch === '.' ? 3.6 : ch === '%' ? 10 : 7.4), 0) + 18;
const tw0 = (t) => [...String(t)].reduce((a, ch) => a + (/[가-힣]/.test(ch) ? 12 : 4), 0);

// ---------------------------------------------------------------- 정리 부품 (문장 대신 쓰는 형식)
// 파스텔 4색: butter · peach · lilac · aqua (판정 색 파랑·초록·빨강과 겹치지 않게 고름)
const TONES = ['butter', 'peach', 'stone', 'amber'];
// 소제목 + 파스텔 아이콘 칩
const h2 = (title) => `<h2 class="hd">${title}</h2>`;
// 소제목 아래 핵심 태그 (문장 대신)
const keys = (arr) => { const xs = arr.filter(Boolean); return xs.length ? `<p class="keys">${xs.join('<span class="sep"> · </span>')}</p>` : ''; };
// 항목 | 내용 목록
const facts = (rows, head = '') => `${head ? `<p class="facts-h">${head}</p>` : ''}<dl class="facts">${rows.filter(Boolean).map(([k, v, s]) => `<dt>${k}</dt><dd>${v}${s ? `<span class="s">${s}</span>` : ''}</dd>`).join('')}</dl>`;
// 지표 타일 (카드 밖, 섹션 안에 나란히)
const tiles = (arr) => `<div class="tiles">${arr.filter(Boolean).map((t, i) => `<div class="tile t-${t.tone || TONES[i % 4]}"><span class="k">${t.k}</span><span class="v num">${t.v}</span>${t.s ? `<span class="s">${t.s}</span>` : ''}</div>`).join('')}</div>`;
// 대결형 막대 비교 (표 대신): 가운데 항목, 왼쪽 A 막대는 왼쪽으로, 오른쪽 B 막대는 오른쪽으로 자란다.
// 가운데 칩 = 두 값의 차이 + 큰 쪽을 가리키는 화살표. 모양(태그 순서)은 값과 상관없이 같게 유지 → 다시 그려도 깜빡이지 않음.
function duel({ heads, tones, rows, fold = 0 }) {
  const side = (r, s, tone) => {
    const n = r[`${s}n`], o = r[s === 'a' ? 'bn' : 'an'];
    const mx = Math.max(Math.abs(n ?? 0), Math.abs(o ?? 0));
    const w = isNum(n) && mx > 0 ? Math.max(Math.abs(n) / mx * 100, 4) : 0;
    return `<div class="bf-s ${s} t-${tone}${r[`${s}neg`] ? ' neg' : ''}"><span class="bv num">${r[s]}</span>${r[`${s}s`] ? `<span class="bs">${r[`${s}s`]}</span>` : ''}${isNum(n) && !r.nobar ? `<span class="bb"><i style="width:${w.toFixed(1)}%"></i></span>` : ''}</div>`;
  };
  const chip = (r) => {
    if (!r.diff) return '';
    const ok = isNum(r.an) && isNum(r.bn);
    const d = ok ? r.an - r.bn : 0, eq = !ok || Math.abs(d) < 1e-9;
    return `<span class="bd${eq ? ' eq' : ''}"><i class="al${!eq && d > 0 ? ' on' : ''}">${icon('chevron-left', 12)}</i><b class="num">${eq ? '같음' : r.diff(Math.abs(d))}</b><i class="ar${!eq && d < 0 ? ' on' : ''}">${icon('chevron-right', 12)}</i></span>`;
  };
  return `<div class="bf">
    <div class="bf-head"><div class="bh a t-${tones[0]}">${heads[0]}</div><span class="vs">VS</span><div class="bh b t-${tones[1]}">${heads[1]}</div></div>
    ${(() => {
      const html = rows.filter((r) => !(r.a === '—' && r.b === '—')).map((r) => `<div class="bf-row">${side(r, 'a', tones[0])}<div class="bf-c"><span class="bl">${r.lab}</span>${r.sub ? `<span class="bsub">${r.sub}</span>` : ''}${chip(r)}</div>${side(r, 'b', tones[1])}</div>`);
      if (!fold || html.length <= fold) return html.join('');
      return html.slice(0, fold).join('') + `<details class="bf-more"><summary>${html.length - fold}개 항목 더 보기 ${icon('chevron-right', 16)}</summary>${html.slice(fold).join('')}</details>`;
    })()}
  </div>`;
}
const dWon = (v) => won(v).replace(/\s원$/, '');
const dPp = (v) => `${v.toFixed(1)}%p`;

// 0을 가운데 둔 가로 막대
function dbar(v, lo, hi) {
  if (!isNum(v)) return '<div class="dbar"></div>';
  const span = hi - lo || 1, z = ((0 - lo) / span) * 100, x = ((v - lo) / span) * 100;
  const left = Math.min(z, x), width = Math.abs(x - z);
  return `<div class="dbar"><div class="z" style="left:${z}%"></div><div class="f ${v < 0 ? 'neg' : 'pos'}" style="left:${left}%;width:${Math.max(width, 0.6)}%"></div></div>`;
}

// ---------------------------------------------------------------- 화면: 회사 찾기
const EXAMPLES = ['현대자동차', '삼성전자', '오뚜기', 'LG유플러스', 'HD현대중공업'];
function viewFind() {
  setTop({ title: '', about: true });
  setTabs(null);
  $view.innerHTML = `
    <div class="find-head">
      <h1>요구안을 받았을 때,<br>어디서 협상을 시작할까</h1>
      ${keys(['업계 비교군 20곳과 비교해 협상 구간과 그 근거, 위험까지 봅니다'])}
    </div>
    <div class="search">
      ${icon('search', 20)}
      <input id="q" type="search" inputmode="search" autocomplete="off" placeholder="회사 이름 또는 종목코드" aria-label="회사 검색">
    </div>
    <div class="examples"><span class="label">예시</span>
      ${EXAMPLES.filter((n) => CTX.list.some((f) => f.name === n)).map((n) => `<button class="chip" data-ex="${esc(n)}">${esc(n)}</button>`).join('')}
    </div>
    <ul class="results" id="res" aria-live="polite"></ul>
    <div class="find-foot">
      <a class="link-row" href="#/about">${icon('info', 20)}<span>데이터와 계산 근거</span></a>
      ${tiles([{ k: 'DART 공시 회사', v: `${CTX.list.length.toLocaleString('ko-KR')}곳`, tone: 'stone' }, { k: '진단 구간', v: `${CTX.meta.start}~${CTX.meta.end}`, tone: 'stone' }])}
    </div>`;
  const $q = document.getElementById('q');
  const $res = document.getElementById('res');
  const run = () => {
    const raw = $q.value.trim();
    const q = raw.replace(/\s+/g, '').toLowerCase();
    if (!q) { $res.innerHTML = ''; return; }
    const hit = CTX.list.filter((f) => f.key.includes(q) || (f.code && f.code.startsWith(q)));
    hit.sort((a, b) => (b.key.startsWith(q) - a.key.startsWith(q)) || (b.size - a.size));
    if (!hit.length) { $res.innerHTML = `<li class="empty"><strong>'${esc(raw)}' 결과 없음</strong>${keys(['회사 이름 일부나 6자리 종목코드로 찾아보세요'])}</li>`; return; }
    $res.innerHTML = hit.slice(0, 30).map((f) => {
      const i = f.name.replace(/\s+/g, '').toLowerCase().indexOf(q);
      const nm = i >= 0 && !/\s/.test(f.name) ? `${esc(f.name.slice(0, i))}<mark>${esc(f.name.slice(i, i + q.length))}</mark>${esc(f.name.slice(i + q.length))}` : esc(f.name);
      return `<li><a class="result" href="#/f/${f.id}"><span class="chip-sq" aria-hidden="true">${esc([...String(f.name).replace(/^\(주\)|^주식회사\s*/, '').trim()][0] || '·')}</span><span class="grow"><span class="name">${nm}</span><span class="meta">${esc(f.ind)}${f.code ? ` · ${f.code}` : ''}</span></span>${icon('chevron-right', 20)}</a></li>`;
    }).join('') + (hit.length > 30 ? `<li class="empty">+${hit.length - 30}곳 더 · 이름을 더 입력해 좁히기</li>` : '');
  };
  $q.addEventListener('input', run);
  $view.querySelectorAll('[data-ex]').forEach((b) => b.addEventListener('click', () => { $q.value = b.dataset.ex; run(); }));
}

// ---------------------------------------------------------------- 화면: 요약·진단
// 디자인 원칙(11-23): 결론은 헤더 한 곳에만, 진한 노랑은 걸친 협상 구간 카드 하나에만, 아래 섹션은 근거(그래프)만.
// 헤더 안 미니 눈금자: 기본급 인상률 한 줄에 뒤처짐(옅은 먹색) · 협상 구간(먹색) · 부담 큼(주황)
function miniRuler(rng) {
  const g = rng['하한'], up = rng['상한'], showMax = CTX.C.RANGE_UPPER_SHOW_MAX;
  if (!isNum(g)) return '';
  const hasUp = isNum(up), ok = hasUp && up >= g, over = hasUp && up > showMax;
  const M = Math.min(Math.ceil(Math.max(0.1, g * 1.5, ok && !over ? up * 1.25 : 0) * 100) / 100, 0.2);
  const p = (x) => clamp(x / M, 0, 1) * 100;
  const xg = p(g), xu = hasUp ? (over ? 100 : p(up)) : 100;
  const seg = ok ? [[0, xg, 'lo'], [xg, xu, 'in'], [xu, 100, 'hi']] : hasUp ? [[0, xg, 'lo'], [xg, 100, 'hi']] : [[0, xg, 'lo'], [xg, 100, 'in hold']];
  return `<div class="mini-ruler" aria-hidden="true">
      <div class="mr-bar">${seg.map(([a, b, c]) => `<i class="mr-${c.split(' ').join(' mr-')}" style="left:${a.toFixed(1)}%;width:${Math.max(b - a, 0).toFixed(1)}%"></i>`).join('')}</div>
      <div class="mr-ticks num"><span>0%</span><span>${Math.round(M * 100)}%</span></div>
    </div>`;
}
function heroCard(f, rng, wc) {
  const state = rng['상한 상태'];
  let line;
  if (state === '비교군 인상률 없음') {
    line = `<a class="rangeline" href="#/f/${f.id}/range"><div class="k">협상 구간</div><div class="v">업계 인상률 넣고 계산 ${icon('chevron-right', 20)}</div><div class="s">하한·상한을 바로 계산</div></a>`;
  } else {
    const hold = state === CTX.C.RANGE_HOLD_TEXT, up = rng['상한'], g = rng['하한'];
    // 상한이 하한보다 낮으면 범위(~)가 거꾸로 읽히므로 둘을 나눠 표시
    const v = hold ? `하한 ${pct(g)}` : up >= g ? `${pct(g)} ~ ${esc(rng['상한 표시'])}` : `하한 ${pct(g)} · 상한 ${esc(rng['상한 표시'])}`;
    const why = hold ? '업계 적자 → 상한 보류'
      : state === '3년 합산 영업적자' ? '3년 적자 → 상한 0%'
        : up >= g ? `${esc(rng['상한 표시'])}까지는 부담이 업계 수준` : '업계만큼 올리면 부담이 업계보다 큼';
    line = `<div class="rangeline">
        <div class="rl-top"><span class="k">협상 구간</span><span class="rl-why">${why}</span></div>
        <div class="v num">${v}</div>
        ${miniRuler(rng)}
        <a class="rl-link" href="#/f/${f.id}/range">노조안·회사안 넣어 보기 ${icon('chevron-right', 18)}</a>
      </div>`;
  }
  const ax = [];
  if (f.wage_pos && f.wage_pos !== '비교 불가' && isNum(f.wage_gap_pct)) {
    ax.push(`<div class="axis"><div class="k">업계 대비 임금</div><div class="v num">${signed(f.wage_gap_pct)}</div><div class="s">${esc(f.wage_pos)}${wc.rank ? ` · ${wc.n}곳 중 ${wc.rank}위` : ''}</div></div>`);
  }
  if (isNum(f.opm_pct)) {
    const sub = f.capacity === '여력 제약' ? u(f.capacity_reason || '제약') : `${isNum(f.opm_ind_pct) ? `업계 ${pctRaw(f.opm_ind_pct)} · ` : ''}${CAP_LABEL[f.capacity] || ''}`;
    ax.push(`<div class="axis"><div class="k">영업이익률 · 3년</div><div class="v num">${pctRaw(f.opm_pct)}</div><div class="s">${esc(sub.replace(/ · $/, ''))}</div></div>`);
  }
  return `<section class="hero" id="hero">
    <h2 class="co">${esc(f.name)}</h2>
    <p class="ind">${esc(f.ind2_name || '')}${f.stock_code ? ` · ${f.stock_code}` : ''}${f.market ? ` · ${esc(f.market)}` : ''}</p>
    ${ax.length ? `<div class="axes${ax.length === 1 ? ' one' : ''}">${ax.join('')}</div>` : ''}
  </section>
  <div class="sheet-lip">
    ${line}
  </div>`;
}

// 한 줄 진단: 판정 두 개(알약) + 핵심 세 줄(아이콘 · 항목 · 값 · 보조)
function diagnosis(f, rng, wc) {
  const wageW = { '임금 높음': '업계보다 높음', '임금 보통': '업계 수준', '임금 낮음': '업계보다 낮음' }[f.wage_pos] || '비교 불가';
  const capW = { '여력 있음': '업계보다 높음', '여력 보통': '업계보다 낮음', '여력 제약': '제약', '판정 불가': '판정 불가' }[f.capacity] || '판정 불가';
  const wage = isNum(f.wage_10k) ? `${Math.round(f.wage_10k).toLocaleString('ko-KR')}만 원` : '—';
  const st0 = rng['상한 상태'];
  const rowsAll = [
    ['users', 'stone', '1인당 급여', wage, '급여총액 ÷ 직원수'],
    ['trending-up', 'amber', '영업이익률 (3년)', isNum(f.opm_pct) ? pctRaw(f.opm_pct) : '', f.capacity === '여력 제약' ? esc(u(f.capacity_reason || '제약')) : isNum(f.opm_ind_pct) ? `업계 ${pctRaw(f.opm_ind_pct)}` : ''],
    ['scale', 'peach', '협상 구간',
      st0 === '비교군 인상률 없음' ? '직접 입력' : st0 === CTX.C.RANGE_HOLD_TEXT ? `하한 ${pct(rng['하한'])}` : `${pct(rng['하한'])} ~ ${esc(rng['상한 표시'])}`,
      st0 === '비교군 인상률 없음' ? '업계 인상률 넣으면 바로 계산' : st0 === CTX.C.RANGE_HOLD_TEXT ? '업계 적자 → 상한 보류' : esc(rng['구간 해석'])],
  ];
  const rows = rowsAll.slice(0, 1);
  const pills = [f.wage_pos && f.wage_pos !== '비교 불가' ? `<span class="vp"><b>임금</b>${wageW}</span>` : '', f.capacity && f.capacity !== '판정 불가' ? `<span class="vp"><b>이익률</b>${capW}</span>` : ''].join('');
  return `<div class="verdict">${pills}</div>
    <ul class="drows">${rows.filter(([, , , v, s]) => v || s).map(([ic, tone, k, v, s]) => `<li><span class="h-ic t-${tone}">${icon(ic, 16)}</span><span class="dk">${k}<span class="s">${s}</span></span><span class="dv num">${v}</span></li>`).join('')}</ul>`;
}

function viewSummary(id) {
  const f = CTX.firms.get(id);
  setTop({ title: f.name, back: '#/', dark: true });
  setTabs(id, '');
  const rng = E.negotiationRange(CTX, id, null);
  const wc = wageChart(f);
  const peers = peersOf(id).filter((p) => isNum(p.w)).sort((a, b) => b.w - a.w);
  const opm = f.opm_pct, ind = f.opm_ind_pct;
  const sc = Math.max(Math.abs(opm || 0), Math.abs(ind || 0), 1) * 1.15;
  const bar = (v, cls) => `<div class="tr"><div class="fi ${cls}${isNum(v) && v < 0 ? ' neg' : ''}" style="width:${isNum(v) ? Math.min(Math.abs(v) / sc * 100, 100) : 0}%"></div></div>`;
  const peerList = peers.length ? `<details class="more inline">
      <summary>비교군 ${peers.length}곳 보기 ${icon('chevron-right', 18)}</summary>
      <ul class="peers-list">${[...peers, ...(isNum(f.w) ? [{ ...f, us: true }] : [])].sort((a, b) => b.w - a.w).map((p, i) => `<li${p.us ? ' class="us"' : ''}>
          <span class="chip-sq num">${i + 1}</span>
          <span class="grow"><span class="t">${esc(p.name)}</span><span class="s">${p.us ? '우리 회사' : p.ind2 === f.ind2 ? '같은 업계' : '다른 업계 분류'}</span></span>
          <span class="num v">${man(p.w)}</span></li>`).join('')}</ul>
      <p class="note" style="margin-top:8px">급여 높은 순 · 1인당 급여 = 급여총액 ÷ 직원수</p>
    </details>` : '';
  $view.innerHTML = `
    ${heroCard(f, rng, wc)}
    <section class="section">
      ${h2('한 줄 진단', 'sliders-horizontal')}
      <div class="panel diag t-butter">${diagnosis(f, rng, wc)}</div>
    </section>
    ${wc.rank ? `<section class="section">
      ${h2('업계 대비 임금 위치', 'users')}
      <div class="panel">
        ${wageHead(f, wc)}
        ${wc.svg}
        <ul class="legend-row">
          <li><i class="sw sw-us"></i>우리 회사</li>
          <li><i class="sw sw-med"></i>업계 중앙</li>
        </ul>
        ${f.wage_pos === '임금 낮음' ? `<div class="turnover">
            <p class="facts-h">임금 위치별 정규직 자발적 이직률 (WPS)</p>
            ${tiles([{ k: '하위 20%', v: '17.8%', tone: 'peach' }, { k: '상위 20%', v: '12.7%', tone: 'stone' }])}
          </div>` : ''}
        ${peerList}
      </div>
    </section>` : ''}
    <section class="section"${isNum(opm) ? '' : ' hidden'}>
      ${h2('업계 대비 이익률', 'trending-up')}
      <div class="panel">
        ${CAP_LABEL[f.capacity] && f.capacity !== '판정 불가' ? `<div class="verdict" style="margin-bottom:14px"><span class="vp"><b>판정</b>${esc(CAP_LABEL[f.capacity])}</span></div>` : ''}
        <div class="bars2">
          <div class="b"><span>우리 회사</span>${bar(opm, '')}<span class="val num">${pctRaw(opm)}</span></div>
          ${isNum(ind) ? `<div class="b"><span>업계 중앙</span>${bar(ind, 'ind')}<span class="val num">${pctRaw(ind)}</span></div>` : ''}
        </div>
        <dl class="kv kv-lines">
          ${isNum(f.labor_ratio_pct) ? `<dt>인건비율 <span>급여 ÷ 매출</span></dt><dd class="num">${pctRaw(f.labor_ratio_pct)}${isNum(f.peer_labor_ratio_pct) ? `<span class="muted"> · 업계 ${pctRaw(f.peer_labor_ratio_pct)}</span>` : ''}</dd>` : ''}
          ${isNum(f.opm_sd_pctp) ? `<dt>이익률 평소 변동</dt><dd class="num">${f.opm_sd_pctp.toFixed(1)}%p</dd>` : ''}
        </dl>
        ${f.cf_flag ? `<ul class="flags">${[f.cf_flag].map((x) => `<li>${icon('circle-alert', 15)}${esc(u(x))}</li>`).join('')}</ul>` : ''}
      </div>
    </section>
    ${!wc.rank && peerList ? `<section class="section"><div class="panel">${peerList}</div></section>` : ''}`;
  bindWageChart($view, wc.items);
  const tb = $view.querySelector('.tip-btn');
  if (tb) tb.addEventListener('click', () => {
    const open = tb.getAttribute('aria-expanded') !== 'true';
    tb.setAttribute('aria-expanded', String(open));
    const ww = $view.querySelector('#wage-warn');
    if (open) fadeShow(ww); else fadeHide(ww);
  });
  // 회사명은 헤더에만. 헤더가 화면 밖으로 나가면 상단바에 이름이 나타난다.
  const hero = document.getElementById('hero');
  $top.classList.add('title-hide');
  if (hero && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(([e]) => {
      if (!document.body.contains(hero)) { io.disconnect(); $top.classList.remove('title-hide'); return; }
      $top.classList.toggle('title-hide', e.isIntersecting);
    }, { rootMargin: '-56px 0px 0px 0px', threshold: 0 });
    io.observe(hero);
  }
}

// ---------------------------------------------------------------- 공통 입력 부품
function stepper(key, val, { step = 0.5, min = 0, max = 50, label }) {
  const neg = min < 0;
  return `<div class="field"><label for="in-${key}">${label}</label>
    <div class="stepper">
      <button type="button" data-step="${key}" data-d="${-step}" aria-label="${label} ${step}%p 내리기">−</button>
      <span class="inp"><input id="in-${key}" data-key="${key}" type="text" inputmode="${neg ? 'text' : 'decimal'}" enterkeyhint="done" autocomplete="off" value="${(val * 100).toFixed(1)}" data-min="${min}" data-max="${max}"><span class="unit">%</span></span>
      <button type="button" data-step="${key}" data-d="${step}" aria-label="${label} ${step}%p 올리기">+</button>
    </div></div>`;
}
function parseNum(s) {
  const t = String(s).trim().replace(/[−–]/g, '-').replace(',', '.');
  if (!/^-?\d*\.?\d*$/.test(t) || t === '' || t === '-' || t === '.' || t === '-.') return NaN;
  return Number(t);
}
function bindSteppers(root, get, set, onChange) {
  root.querySelectorAll('[data-step]').forEach((b) => b.addEventListener('click', () => {
    const k = b.dataset.step, inp = root.querySelector(`[data-key="${k}"]`);
    const v = Math.round((get(k) * 100 + Number(b.dataset.d)) * 10) / 10;
    const c = clamp(v, Number(inp.dataset.min), Number(inp.dataset.max));
    set(k, c / 100); inp.value = c.toFixed(1); onChange();
  }));
  root.querySelectorAll('input[data-key]').forEach((inp) => {
    // 입력하는 즉시 그래프와 표를 다시 계산하고, 칸을 벗어날 때 표시를 정리한다
    inp.addEventListener('input', () => {
      const n = parseNum(inp.value);
      if (!Number.isFinite(n)) return;
      set(inp.dataset.key, clamp(n, Number(inp.dataset.min), Number(inp.dataset.max)) / 100);
      onChange();
    });
    const tidy = () => { inp.value = (get(inp.dataset.key) * 100).toFixed(1); };
    inp.addEventListener('change', tidy);
    inp.addEventListener('blur', tidy);
    inp.addEventListener('focus', () => inp.select());
  });
}

// ---------------------------------------------------------------- 화면: 인상안 협상 구간
function viewRange(id) {
  const f = CTX.firms.get(id);
  const S = st(id);
  setTop({ title: f.name, back: '#/' });
  setTabs(id, '/range');
  const rng0 = E.negotiationRange(CTX, id, S.override);
  if (rng0['상한 상태'] === '비교군 인상률 없음' && S.override === null) {
    $view.innerHTML = `<section class="section">${h2('인상안 협상 구간', 'scale', 'peach')}
      <div class="panel t-butter">${facts([['방법', '업계 인상률 직접 입력', '넣는 즉시 하한·상한 계산']])}</div>
      <button class="btn" type="button" id="ovon" style="margin-top:12px">업계 인상률 직접 넣기</button></section>`;
    document.getElementById('ovon').addEventListener('click', () => { S.override = 0.04; viewRange(id); });
    return;
  }
  const ov = S.override;
  $view.innerHTML = `
    <section class="section" style="margin-top:12px">
      ${h2('인상안 협상 구간', 'scale', 'peach')}
      ${keys(['하한은 노측, 상한은 사측 협상 근거입니다'])}
      <div class="panel" id="chartbox"></div>
      <details class="more panel">
        <summary><span class="sum-l">하한·상한 정하는 법</span>${icon('chevron-right', 18)}</summary>
        ${facts([
          ['하한', '<strong>업계 인상률</strong>', '비교군 20곳 · 최근 3년 1인당 급여 연 증가율 중앙값'],
          ['하한보다 낮으면', '업계 대비 임금 위치 하락', '임금 위치 낮을수록 자발적 이직 많음 (WPS)'],
          ['상한', '<strong>업계와 같은 부담 수준</strong>', '검은 선(우리 부담) × 점선(업계 부담) 교차점'],
          ['상한의 의미', '감당 한도 아님 · 업계 기준선', '이익이 급여 대비 크면 상한 ↑'],
        ])}
      </details>
    </section>
    <section class="section">
      ${h2('두 안 넣기', 'sliders-horizontal', 'stone')}
      <div class="offer t-butter"><div class="offer-head"><h3>노조안</h3></div>
        <div class="fields">${stepper('ub', S.union.base, { label: '기본급 인상률' })}${stepper('ux', S.union.bonus, { label: '일시 성과급(급여 대비)' })}</div></div>
      <div class="offer t-stone"><div class="offer-head"><h3>회사안</h3></div>
        <div class="fields">${stepper('cb', S.company.base, { label: '기본급 인상률' })}${stepper('cx', S.company.bonus, { label: '일시 성과급(급여 대비)' })}</div></div>
      <details class="more panel">
        <summary><span class="sum-l">두 안 공통 가정</span>${icon('chevron-right', 18)}</summary>
        ${sw('ov', ov !== null, '업계 인상률 직접 입력', '켜면 하한·상한을 이 값으로 다시 계산')}
        <div id="ovf" ${ov === null ? 'hidden' : ''}>${stepper('ov', ov ?? (isNum(f.peer_growth) ? f.peer_growth : 0.04), { label: '업계 인상률', step: 0.1, max: 30 })}</div>
        <hr class="divider">
        <div class="fields">${stepper('hc', S.headcount, { label: '인원 증감', min: -50, max: 50 })}${stepper('sg', S.sales, { label: '매출 증가율', min: -80, max: 100 })}</div>
        ${facts([['신규 인원 급여', '지금 1인당 평균'], ['늘어난 매출', '지금 영업이익률 유지'], ['불황 영향', '미래 위험 탭에서']])}
      </details>
    </section>
    <section class="section">
      ${h2('두 안 비교', 'git-compare-arrows', 'butter')}
      <div class="panel" id="cmpbox"></div>
      <div class="row" style="margin-top:12px;gap:10px">
        <a class="btn secondary half" href="#/f/${id}/link">${icon('coins', 18)}이익 기준 환산</a>
        <a class="btn secondary half" href="#/f/${id}/risk">${icon('cloud-lightning', 18)}불황이 오면</a>
      </div>
    </section>`;

  const get = (k) => ({ ub: S.union.base, ux: S.union.bonus, cb: S.company.base, cx: S.company.bonus, hc: S.headcount, sg: S.sales, ov: S.override ?? 0.04 }[k]);
  const set = (k, v) => {
    if (k === 'ub') S.union.base = v; else if (k === 'ux') S.union.bonus = v;
    else if (k === 'cb') S.company.base = v; else if (k === 'cx') S.company.bonus = v;
    else if (k === 'hc') S.headcount = v; else if (k === 'sg') S.sales = v; else if (k === 'ov') S.override = v;
  };
  const draw = () => {
    const rng = E.negotiationRange(CTX, id, S.override);
    const plan = { headcount: S.headcount, sales_growth: S.sales, peer_raise: S.override };
    const t = E.compareOffers(CTX, id, { base_raise: S.union.base, bonus: S.union.bonus }, { base_raise: S.company.base, bonus: S.company.bonus }, plan);
    const R = (k) => t.rows[k];
    const state = rng['상한 상태'];
    let interp;
    const callout = (ic, title, tags, tone = '') => `<div class="callout${tone}">${icon(ic, 18)}<div><strong>${title}</strong>${keys(tags)}</div></div>`;
    if (state === CTX.C.RANGE_HOLD_TEXT) interp = callout('circle-alert', '업계가 적자라 상한은 계산하지 않았습니다', ['하한만 참고하고, 기준 환산 탭에서 이익 기준 성과급을 검토해 보세요'], ' neutral');
    else if (state === '3년 합산 영업적자') interp = callout('circle-alert', '3년 합산 영업적자라 상한은 0%입니다', ['기준 환산 탭에서 이익 기준 성과급을 검토해 보세요']);
    else interp = callout('scale', esc(RANGE_MSG[rng['구간 해석']] || rng['구간 해석']), [
      state === '적자 전환 직전에서 제한' ? '마지막 해 영업이익 한도에서 멈췄습니다' : '',
      rng['상한'] > CTX.C.RANGE_UPPER_SHOW_MAX ? '상한이 10%를 넘어 "10% 초과"로 표시합니다' : '',
    ]);
    const pos = (k) => `<span class="badge ${posClass(R('구간 위치')[k])}"><span class="dot"></span>${esc(R('구간 위치')[k])}</span>`;
    const $cb = document.getElementById('chartbox');
    enterOnce($cb);
    morph($cb, `${rangeChart(f, rng, { union: S.union.base, company: S.company.base })}
      <div class="pos-row"><div><span class="k">노조안</span>${pos('노조안')}</div><div><span class="k">회사안</span>${pos('회사안')}</div></div>
      <div style="margin-top:12px">${interp}</div>`);
    const rank = (v) => (isNum(v) ? `상위 ${Math.max(1, Math.round((1 - v) * 100))}%` : '—');
    const two = (key, fmt, extra = {}) => {
      const a = R(key)['노조안'], b = R(key)['회사안'];
      return { a: fmt(a), b: fmt(b), an: a, bn: b, aneg: isNum(a) && a < 0, bneg: isNum(b) && b < 0, ...extra };
    };
    const dz = (v) => (v ? '<span class="badge above">적자 전환</span>' : '<span class="badge inside">흑자 유지</span>');
    // 내년 업계 중앙 급여 = 내년 우리 1인당 급여 ÷ (1 + 업계 중앙 대비 차이)
    const nU = R('내년 1인당 급여')['노조안'], gU = R('내년 예상 임금 차이(%)')['노조안'];
    const medNext = isNum(nU) && isNum(gU) ? nU / (1 + gU / 100) : NaN;
    const head = (who, o) => `<span class="bt">${who}</span><span class="bi num">기본급 ${pct(o.base)}<br>성과급 ${pct(o.bonus)}</span>${pos(who)}`;
    morph(document.getElementById('cmpbox'), `
      ${duel({ heads: [head('노조안', S.union), head('회사안', S.company)], tones: ['butter', 'stone'], fold: 3, rows: [
        { lab: '회사 부담 증가', sub: '1년', ...two('회사 부담 증가(1년)', won), diff: dWon },
        { lab: '내년 1인당 급여', sub: '성과급 포함', ...two('내년 1인당 급여', man), diff: (v) => man(v).replace(/\s원$/, '') },
        { lab: '업계 중앙보다', sub: isNum(medNext) ? `내년 업계 중앙 ${man(medNext)}` : '내년 업계 중앙 대비', ...two('내년 예상 임금 차이(%)', signed), as: rank(R('내년 예상 순위')['노조안']), bs: rank(R('내년 예상 순위')['회사안']), aneg: false, bneg: false, nobar: true, diff: dPp },
        { lab: '3년 누적 부담', sub: '성과급 1회 포함', ...two('3년 누적 부담(인원·기본급 유지 + 성과급 1회)', won), diff: dWon },
        { lab: '비용 ÷ 영업이익', ...two('비용÷영업이익(%)', pctRaw), diff: dPp },
        { lab: '내년 영업이익률', ...two('내년 영업이익률(%)', pctRaw), diff: dPp },
        { lab: '지급 후 이익', a: dz(R('지급 때문에 적자 전환')['노조안']), b: dz(R('지급 때문에 적자 전환')['회사안']) },
      ] })}
      <p class="facts-h">계산 기준</p>
      <dl class="facts">
        <dt>기본급 인상</dt><dd>4대보험·퇴직금 약 18.3% 포함</dd>
        <dt>일시 성과급</dt><dd>4대보험 10% 포함</dd>
        ${isNum(R('비교군 인상률 가정')['노조안']) ? `<dt>내년 임금 가정</dt><dd>비교군도 업계 인상률 <span class="num">${pct(R('비교군 인상률 가정')['노조안'])}</span>만큼 인상</dd>` : ''}
      </dl>`);
  };
  bindSteppers($view, get, set, draw);
  $view.querySelector('[data-sw="ov"]').addEventListener('change', (e) => {
    S.override = e.target.checked ? (isNum(f.peer_growth) ? Math.round(f.peer_growth * 1000) / 1000 : 0.04) : null;
    const fld = document.getElementById('ovf');
    fld.hidden = !e.target.checked;
    if (e.target.checked) fld.querySelector('input').value = (S.override * 100).toFixed(1);
    draw();
  });
  draw();
}
function sw(key, on, title, desc = '') {
  return `<div class="switch-row"><div><div class="t" id="lb-${key}">${title}</div>${desc ? `<div class="d">${desc}</div>` : ''}</div>
    <label class="switch"><input type="checkbox" data-sw="${key}" ${on ? 'checked' : ''} aria-labelledby="lb-${key}"><span></span></label></div>`;
}

// ---------------------------------------------------------------- 화면: 급여 기준 ↔ 이익 기준 환산 (기능 3)
// 지금 성과급 입력값 → 엔진 인자 (급여 대비 % 또는 올해 총액)
function linkArgs(S) {
  return S.link.mode === 'amount' && isNum(S.link.amount) ? { amount: S.link.amount } : { rate: S.link.rate };
}
// 기능 4로 넘길 급여 대비 비율 (총액 입력이면 마지막 해 급여총액으로 나눔)
function linkRate(id) {
  return E.profitLinkPlan(CTX, id, linkArgs(st(id)))['현재 지급률(급여 대비)'];
}

function viewLink(id) {
  const f = CTX.firms.get(id);
  const S = st(id);
  setTop({ title: f.name, back: '#/' });
  setTabs(id, '/link');
  const L = S.link;
  const eok = isNum(L.amount) ? String(Math.round(L.amount / 1e8)) : (isNum(f.S_T) ? String(Math.round((L.rate * f.S_T) / 1e8)) : '');
  $view.innerHTML = `
    <section class="section" style="margin-top:12px">
      ${h2('급여 기준 ↔ 이익 기준 환산', 'coins', 'butter')}
      ${keys(['지금 성과급은 영업이익 비율로, 노조 요구는 급여 비율로 바꿔 봅니다', '3년 연평균 기준'])}
    </section>
    <section class="section">
      <div class="panel">
        <p class="facts-h" style="margin:0 0 10px">지금 주는 성과급</p>
        <div class="seg" role="group" aria-label="입력 방식">
          <button type="button" data-mode="rate" aria-pressed="${L.mode !== 'amount'}">급여의 %</button>
          <button type="button" data-mode="amount" aria-pressed="${L.mode === 'amount'}">올해 총액</button>
        </div>
        <div style="margin-top:12px">
          <div id="m-rate" ${L.mode === 'amount' ? 'hidden' : ''}>${stepper('lr', L.rate, { label: '급여 대비 성과급', step: 0.5, max: 200 })}</div>
          <div id="m-amount" ${L.mode === 'amount' ? '' : 'hidden'}><div class="field"><label for="in-amt">올해 성과급 총액</label>
            <div class="stepper"><span class="inp" style="grid-column:1 / -1"><input id="in-amt" type="text" inputmode="decimal" enterkeyhint="done" autocomplete="off" value="${eok}"><span class="unit">억 원</span></span></div></div></div>
        </div>
        <div style="margin-top:10px">${keys(['기본값은 급여의 5%입니다'])}</div>
      </div>
    </section>
    <section class="section">
      ${h2('같은 금액이 되는 영업이익 비율', 'scale', 'amber')}
      <div class="panel" id="conv"></div>
    </section>
    <section class="section">
      ${h2('노조 요구를 급여로 환산', 'users', 'peach')}
      <div class="panel">
        ${stepper('dn', L.demand, { label: '노조 요구(영업이익 대비)', step: 1, max: 100 })}
        <div class="row" style="gap:8px;margin-top:10px;flex-wrap:wrap">${[0.10, 0.15, 0.30].map((v) => `<button class="chip" type="button" data-dn="${v}">영업이익의 ${pct(v, 0)}</button>`).join('')}</div>
        <div id="dres" style="margin-top:16px"></div>
      </div>
    </section>
    <section class="section" id="lrisk-sec">
      ${h2('이익 기준으로 바꾸면 (3년)', 'cloud-lightning', 'stone')}
      ${keys(['이익이 줄면 회사 부담도 줄지만, 직원이 받는 돈은 해마다 달라집니다'])}
      <div class="panel" id="lrisk"></div>
      <a class="btn secondary" href="#/f/${id}/risk" style="margin-top:12px">${icon('cloud-lightning', 18)}불황이 오면 이익 기준 성과급은?</a>
    </section>`;

  const draw = () => {
    const args = linkArgs(S);
    const r = E.profitLinkPlan(CTX, id, args);
    const rate = r['현재 지급률(급여 대비)'];
    const aEq = r['같은 금액 비율(3년 평균 기준)'], aT = r['같은 금액 비율(작년 기준)'];
    let gap = '';
    if (isNum(aEq) && isNum(aT) && Math.abs(aT / aEq - 1) >= 0.2) {
      gap = aT < aEq
        ? `<div class="callout neutral" style="margin-top:12px">${icon('circle-alert', 18)}<div><strong>작년 이익이 3년 평균보다 큽니다</strong>${keys(['작년 기준으로 합의하면 이익이 평년으로 돌아올 때 성과급이 줄어듭니다'])}</div></div>`
        : `<div class="callout neutral" style="margin-top:12px">${icon('circle-alert', 18)}<div><strong>작년 이익이 3년 평균보다 작습니다</strong>${keys(['작년 기준으로 합의하면 이익이 회복될 때 성과급이 크게 늘어납니다'])}</div></div>`;
    }
    morph(document.getElementById('conv'), isNum(aEq) && f.OP_avg > 0 ? `
      <div class="card-top"><span class="cap">급여의 ${pct(rate)}와 같은 금액</span></div>
      <p class="wage-claim num"><span class="big-unit">영업이익의</span><span class="big-num">${pct(aEq)}</span></p>
      ${tiles([
        { k: '3년 평균 기준 · 권장', v: pct(aEq), tone: 'butter' },
        isNum(aT) ? { k: '작년 한 해 기준', v: pct(aT), tone: 'stone' } : null,
        { k: '1년 성과급', v: won(r['고정 지급(급여 대비 rate)']), s: `1인당 ${man(r['1인당 고정 지급'])}`, tone: 'amber' },
      ])}
      ${gap}`
      : facts([['3년 합산 영업적자', '같은 금액 비율 계산 불가'], ['이익 기준으로 바꾸면', '이익 날 때까지 성과급 0원']]));

    const d = E.demandToSalary(CTX, id, { n: L.demand, ...args });
    const k = d['요구 ÷ 현재'];
    morph(document.getElementById('dres'), f.OP_avg > 0 ? `
      <div class="card-top"><span class="cap">영업이익의 ${pct(L.demand, 0)}는</span></div>
      <p class="wage-claim num"><span class="big-unit">급여의</span><span class="big-num">${pctRaw(d['요구 급여 대비 지급률(%)'])}</span></p>
      ${tiles([
        { k: '1년 총액', v: won(d['요구 지급']), tone: 'peach' },
        { k: '1인당', v: man(d['1인당 요구 지급']), tone: 'stone' },
        isNum(k) ? { k: '지금 성과급의', v: `${k.toFixed(1)}배`, tone: 'butter' } : null,
      ])}`
      : facts([['3년 합산 영업적자', '요구액 0원']]));

    // 3년 모델 예측: 0원인 해·흔들림은 비율과 무관, 비용은 지급률에 비례 (예측 대상이 아니면 섹션을 숨김)
    const fr = CTX.fc.get(id);
    const K = '3년·같은 예산 이익연동(α)_', X = '3년·급여총액 5%_';
    const sc = rate / CTX.C.PAY_RATE;
    const ok = !!fr && isNum(fr[`${K}0원인 해 생김`]);
    document.getElementById('lrisk-sec').hidden = !ok;
    if (!ok) return;
    const cost = (v) => (isNum(v) ? v * 1e8 * sc : NaN);
    const pp = (v) => `${(v * 100).toFixed(0)}%p`;
    const row = (lab, sub, key) => ({ lab, sub, a: pct(fr[X + key], 0), b: pct(fr[K + key], 0), an: fr[X + key], bn: fr[K + key], diff: pp });
    const rowC = (lab, sub, key) => { const a = cost(fr[X + key]), b = cost(fr[K + key]); return { lab, sub, a: won(a), b: won(b), an: a, bn: b, diff: dWon }; };
    morph(document.getElementById('lrisk'), duel({ heads: ['지금 · 급여 기준', '이익 기준'], tones: ['stone', 'butter'], rows: [
      row('성과급 0원인 해', '3년 안에 생길 확률', '0원인 해 생김'),
      { ...row('1인당 수령액 흔들림', '해마다 평균에서 벗어나는 폭', '1인당 수령 변동계수'), a: `±${pct(fr[X + '1인당 수령 변동계수'], 0)}`, b: `±${pct(fr[K + '1인당 수령 변동계수'], 0)}` },
      rowC('3년 비용', '보통', '3년 비용 P50(억)'),
      rowC('3년 비용', '많을 때', '3년 비용 P90(억)'),
    ] }));
  };

  const get = (k) => (k === 'lr' ? L.rate : L.demand);
  const set = (k, v) => { if (k === 'lr') L.rate = v; else L.demand = v; };
  bindSteppers($view, get, set, draw);
  $view.querySelectorAll('[data-mode]').forEach((b) => b.addEventListener('click', () => {
    L.mode = b.dataset.mode;
    $view.querySelectorAll('[data-mode]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    document.getElementById('m-rate').hidden = L.mode === 'amount';
    document.getElementById('m-amount').hidden = L.mode !== 'amount';
    if (L.mode === 'amount' && !isNum(L.amount)) { const n = parseNum(document.getElementById('in-amt').value); if (Number.isFinite(n) && n > 0) L.amount = n * 1e8; }
    draw();
  }));
  document.getElementById('in-amt').addEventListener('input', (e) => {
    const n = parseNum(e.target.value);
    if (Number.isFinite(n) && n > 0) { L.amount = n * 1e8; draw(); }
  });
  $view.querySelectorAll('[data-dn]').forEach((b) => b.addEventListener('click', () => {
    L.demand = Number(b.dataset.dn);
    document.getElementById('in-dn').value = (L.demand * 100).toFixed(1);
    draw();
  }));
  draw();
}

// ---------------------------------------------------------------- 화면: 미래 위험
const COMMON_DESC = {
  코로나형: '2020년 코로나19 확산 때 각 업계가 실제로 겪은 영업이익률·매출 변화를 다시 적용합니다.',
  '원자재·금리형': '2022년 원자재 가격 급등과 금리 인상 때 각 업계가 실제로 겪은 변화를 다시 적용합니다.',
};
// 사건 설명을 문장·쉼표(괄호 밖) 단위로 나눠 짧은 항목 목록으로
function descList(t) {
  const parts = [];
  for (const sen of String(t).split(/(?<=[.。])\s+/)) {
    let depth = 0, cur = "";
    for (let i = 0; i < sen.length; i++) {
      const c = sen[i];
      if (c === "(") depth++; else if (c === ")") depth = Math.max(0, depth - 1);
      if (c === "," && sen[i + 1] === " " && depth === 0) { parts.push(cur); cur = ""; i++; continue; }
      cur += c;
    }
    parts.push(cur);
  }
  const items = parts.map((x) => x.trim().replace(/[.。]$/, "")).filter(Boolean);
  return items.length > 1 ? `<ul class="scn-desc">${items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : esc(items[0] || "");
}
function scnInfo(name, kind) {
  if (kind === '직접 입력') return { desc: '직접 정한 영업이익률·매출 변화를 적용합니다.', src: [] };
  if (kind === '최악의 해') return { desc: '우리 업계의 영업이익률이 가장 크게 떨어졌던 해의 변화를 다시 적용합니다.', src: [] };
  for (const [k, d] of Object.entries(COMMON_DESC)) if (name.startsWith(k)) return { desc: d, src: [] };
  const row = (CTX.catalog || []).find((r) => name.startsWith(`${r['사건명']} (${r['연도']})`));
  if (!row) return { desc: '', src: [] };
  const src = String(row['출처'] || '').split(' | ').filter((x) => /^https?:\/\//.test(x)).slice(0, 2);
  // 설명 중 근거의 한계를 말하는 문장(분리 근거 없음·다른 요인과 섞임 등)은 화면에서 뺀다
  const desc = u(row['원인근거'] || '').split(/(?<=[.。])\s+/)
    .filter((s) => !/근거(는|가)?\s*없|분리|섞여|미확인|불확실|아닐 수|확인되지|찾지 못/.test(s)).join(' ').trim();
  return { desc, src, level: row['확인수준'] };
}

function viewRisk(id) {
  const f = CTX.firms.get(id);
  const S = st(id);
  setTop({ title: f.name, back: '#/' });
  setTabs(id, '/risk');
  const plan = { base_raise: S.company.base, bonus: S.company.bonus };
  const sc = E.scenarios(CTX, id);
  if (!S.risk.pick || (S.risk.pick !== '직접 입력' && !sc.some((x) => x['경우'] === S.risk.pick))) {
    const pref = sc.find((x) => x['종류'] === '우리 업종 사건') || sc.find((x) => x['종류'] === '최악의 해') || sc[0];
    S.risk.pick = pref ? pref['경우'] : '직접 입력';
  }
  const groups = ['우리 업종 사건', '최악의 해', '공통 사건'];
  const opts = groups.map((gname) => {
    const xs = sc.filter((x) => x['종류'] === gname);
    if (!xs.length) return '';
    return `<optgroup label="${esc(SCN_KIND[gname])}">${xs.map((x) => `<option value="${esc(x['경우'])}" ${S.risk.pick === x['경우'] ? 'selected' : ''}>${esc(shortScn(x['경우']))}</option>`).join('')}</optgroup>`;
  }).join('') + `<optgroup label="직접 입력"><option value="직접 입력" ${S.risk.pick === '직접 입력' ? 'selected' : ''}>직접 충격 정하기</option></optgroup>`;

  $view.innerHTML = `
    <section class="section" style="margin-top:12px">
      ${h2('미래 위험', 'cloud-lightning', 'amber')}
      ${keys([`회사안 기본급 ${pct(S.company.base)}, 성과급 ${pct(S.company.bonus)} 기준`, `지금 성과급(급여의 ${pct(linkRate(id))})은 이익 기준으로 환산`, `<a href="#/f/${id}/range">회사안 바꾸기</a>`])}
      <div class="panel" id="fcbox"></div>
    </section>
    <section class="section" id="stress">
      ${h2('업계 불황 대비 점검', 'circle-alert', 'peach')}
      ${keys(['우리 업계가 실제로 겪은 불황을 내년에 다시 적용합니다'])}
      <div class="panel t-peach">
        <label class="pick-label" for="pick">어떤 불황을 볼까요</label>
        <div class="pick">${icon('cloud-lightning', 18)}<select id="pick">${opts}</select>${icon('chevron-right', 18, 'pick-chev')}</div>
        <div id="cuf" ${S.risk.pick === '직접 입력' ? '' : 'hidden'} style="margin-top:12px"><div class="fields">${stepper('dm', S.risk.dm, { label: '영업이익률 변화(%p)', min: -50, max: 20 })}${stepper('dr', S.risk.dr, { label: '매출 변화', min: -90, max: 50, step: 1 })}</div></div>
        <div class="seg" role="group" aria-label="충격 크기" style="margin-top:14px">
          <button type="button" data-sev="중앙" aria-pressed="${S.risk.severity === '중앙'}">보통 타격<span class="sub">업계 중간 수준</span></button>
          <button type="button" data-sev="하위25" aria-pressed="${S.risk.severity === '하위25'}">큰 타격<span class="sub">하위 25% 수준</span></button>
        </div>
        ${sw('ws', S.risk.withSales, '매출 감소도 함께', '끄면 영업이익률 변화만 적용')}
      </div>
      <div id="warn"></div>
      <div class="panel" id="scnbox" style="margin-top:12px"></div>
    </section>`;

  const drawFc = () => {
    const t = E.payPlanForecast(CTX, id, plan);
    const p = t.attrs['다음 해 적자 확률'];
    let body = '';
    if (!t.order.length) body = `<p class="note" style="margin-top:8px">${esc(t.attrs['안내'] || '')}</p>`;
    else {
      const rows = [['최악의 시나리오', '나쁜 쪽(P10)'], ['보통 시나리오', '중앙(P50)'], ['최적의 시나리오', '좋은 쪽(P90)']].map(([lab, k]) => [lab, t.rows[k]]);
      const vals = rows.map(([, r]) => r['지급 후 영업이익률(%)']).filter(isNum);
      const lo = Math.min(0, ...vals) * 1.15 - 0.5, hi = Math.max(0, ...vals) * 1.15 + 0.5;
      body = `<hr class="divider"><p class="small" style="font-weight:600">회사안을 지급한 뒤 내년 영업이익률</p>
        <ul class="sbars">${rows.map(([lab, r]) => `<li><span class="lab">${lab}</span>${dbar(r['지급 후 영업이익률(%)'], lo, hi)}<span class="val num${r['지급 후 영업이익률(%)'] < 0 ? ' neg' : ''}">${pctRaw(r['지급 후 영업이익률(%)'])}</span></li>`).join('')}</ul>
        ${tiles([{ k: '최악일 때 지급 후 영업이익', v: won(rows[0][1]['지급 후 영업이익']), s: rows[0][1]['지급 때문에 적자 전환'] ? '지급 때문에 적자 전환' : rows[0][1]['지급 후 적자'] ? '지급 전부터 적자' : '흑자 유지', tone: rows[0][1]['지급 때문에 적자 전환'] ? 'peach' : 'amber' }])}`;
    }
    const $fc = document.getElementById('fcbox');
    enterOnce($fc);
    morph($fc, `<div class="prob"><span class="v num">${isNum(p) ? `${Math.round(p * 100)}%` : '—'}</span><span class="muted small">지금 방식대로일 때 다음 해 영업적자 확률</span></div>${body}
      <div style="margin-top:14px">${keys(['최악·최적은 하위·상위 10% 경우입니다'])}</div>`);
    const pv = $fc.querySelector('.prob .v');
    if (pv && isNum(p)) countUp(pv, Math.round(p * 100), 400, (v) => `${Math.round(v)}%`);
  };
  const draw = () => {
    const custom = S.risk.pick === '직접 입력' ? { 이익률: S.risk.dm, 매출: S.risk.dr } : null;
    const t = E.stressTest(CTX, id, { ...plan, severity: S.risk.severity, with_sales: S.risk.withSales, rate: linkRate(id), custom, useForecast: false });
    morph(document.getElementById('warn'), t.attrs['기준 연도 경고'] ? `<ul class="flags" style="margin-top:12px"><li>${icon('circle-alert', 15)}${esc(t.attrs['기준 연도 경고'])}</li></ul>` : '');
    const base = t.rows['평상시'];
    // 공시 매출이 없어 계산할 수 없는 회사는 이 섹션을 숨긴다
    const can = isNum(base['지급 후 영업이익률(%)']);
    document.getElementById('stress').hidden = !can;
    if (!can) return;
    const r = t.rows[S.risk.pick];
    const $box = document.getElementById('scnbox');
    if (!r) { morph($box, facts([['계산 불가', '이 불황의 우리 업계 충격 자료 없음'], ['방법', '다른 불황 고르기']])); return; }
    enterOnce($box);
    const info = scnInfo(S.risk.pick, r['종류']);
    const flag = r['지급 때문에 적자 전환'] ? '<span class="badge above">지급 때문에 적자</span>' : r['지급 후 적자'] ? '<span class="badge hold">원래도 적자</span>' : '<span class="badge inside">흑자 유지</span>';
    const shock = isNum(r['영업이익률 변화(%p)']) ? `업계 영업이익률 ${signed(r['영업이익률 변화(%p)'], 1, '%p')}${isNum(r['매출 변화(%)']) && r['매출 변화(%)'] !== 0 ? ` · 매출 ${signed(r['매출 변화(%)'])}` : ''}` : '';
    const v0 = base['지급 후 영업이익률(%)'], v1 = r['지급 후 영업이익률(%)'];
    const lo = Math.min(0, v0, v1) * 1.15 - 0.5, hi = Math.max(0, v0, v1) * 1.15 + 0.5;
    const ratio = (x) => (isNum(x) ? (x === 0 ? '0원' : `${x.toFixed(2)}배`) : '—');
    morph($box, `
      <div class="scn-head"><div><h3 class="scn-title">${esc(scnLabel(S.risk.pick))}</h3>${keys([esc(SCN_KIND[r['종류']] || r['종류']), esc(u(r['충격 단위'] || ''))])}</div>${flag}</div>
      ${facts([
        info.desc ? ['사건 개요', descList(info.desc)] : null,
        shock ? ['충격 크기', `<span class="scn-shock">${esc(shock)}</span>`] : null,
        
      ])}
      <hr class="divider">
      <p class="facts-h">회사안 지급 후 내년 영업이익률</p>
      <ul class="sbars">
        <li><span class="lab">${scnName('평상시')}</span>${dbar(v0, lo, hi)}<span class="val num${v0 < 0 ? ' neg' : ''}">${pctRaw(v0)}</span></li>
        <li><span class="lab">불황 발생</span>${dbar(v1, lo, hi)}<span class="val num${v1 < 0 ? ' neg' : ''}">${pctRaw(v1)}</span></li>
      </ul>
      <div style="margin-top:14px">${duel({ heads: [scnName('평상시'), '불황 발생'], tones: ['stone', 'peach'], rows: [
        { lab: '지급 후 영업이익', a: won(base['지급 후 영업이익']), b: won(r['지급 후 영업이익']), an: base['지급 후 영업이익'], bn: r['지급 후 영업이익'], aneg: base['지급 후 영업이익'] < 0, bneg: r['지급 후 영업이익'] < 0, diff: dWon },
        { lab: '내년 매출', a: won(base['내년 매출']), b: won(r['내년 매출']), an: base['내년 매출'], bn: r['내년 매출'], diff: dWon },
        { lab: '이익 기준 성과급', sub: '지금 대비', a: ratio(base['이익연동 ÷ 고정']), b: ratio(r['이익연동 ÷ 고정']), an: base['이익연동 ÷ 고정'], bn: r['이익연동 ÷ 고정'], diff: (v) => `${v.toFixed(2)}배` },
      ] })}</div>`);
  };
  document.getElementById('pick').addEventListener('change', (e) => {
    S.risk.pick = e.target.value;
    document.getElementById('cuf').hidden = S.risk.pick !== '직접 입력';
    draw();
  });
  $view.querySelectorAll('[data-sev]').forEach((b) => b.addEventListener('click', () => {
    S.risk.severity = b.dataset.sev;
    $view.querySelectorAll('[data-sev]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
    draw();
  }));
  $view.querySelector('[data-sw="ws"]').addEventListener('change', (e) => { S.risk.withSales = e.target.checked; draw(); });
  bindSteppers($view, (k) => S.risk[k], (k, v) => { S.risk[k] = v; }, draw);
  drawFc();
  draw();
}

// ---------------------------------------------------------------- 화면: 계산 근거
function viewAbout() {
  setTop({ title: '계산 근거', back: LAST_FIRM ? `#/f/${LAST_FIRM}` : '#/', about: false });
  setTabs(null);
  const nEvents = new Set((CTX.catalog || []).filter((r) => r['확인수준'] !== '원인 미확인').map((r) => r['사건ID'])).size;
  const card = (title, ic, tone, body) => `<section class="section">${h2(title, ic, tone)}<div class="panel">${body}</div></section>`;
  $view.innerHTML = `<article class="about">
    ${card('데이터', 'info', 'butter', facts([
      ['출처', 'DART 공시 패널 2015~2025'],
      ['대상', `직원 10명 이상 비금융 ${CTX.list.length.toLocaleString('ko-KR')}곳`],
      ['진단 구간', `${CTX.meta.start}~${CTX.meta.end}년`],
      ['급여 · 이익', '공시 급여총액 · 별도 영업이익'],
      ['계산 규칙', '팀 산술식(formula.py) 하나', '앱 숫자와 일치 여부 자동 검사'],
    ]))}
    ${card('협상 구간', 'scale', 'peach', facts([
      ['하한', '<strong>업계 인상률</strong>', '비교군 20곳 · 최근 3년 1인당 급여 연 증가율 중앙값'],
      ['상한', '<strong>업계와 같은 부담 수준</strong>', '인상 비용 ÷ 영업이익이 비교군과 같아지는 인상률'],
      ['상한의 의미', '감당 한도 아님 · 업계 기준선'],
      ['표시 규칙', '10% 초과 → "10% 초과"', '비교군 대부분 적자 → "상한 산출 보류"'],
      ['노조안·회사안', '사용자가 넣는 안 · 그래프 위 점'],
    ]))}
    ${card('실증 근거 · WPS 2015~2023', 'users', 'stone', `${tiles([{ k: '임금 위치 하위 20% 이직률', v: '17.8%', tone: 'peach' }, { k: '상위 20% 이직률', v: '12.7%', tone: 'amber' }])}
      ${facts([
        ['임금 10% ↑', '정규직 자발적 이직률 0.45%p ↓'],
        ['1인당 급여', '급여총액 ÷ 직원수'],
      ])}`)}
    ${card('미래 위험', 'cloud-lightning', 'amber', facts([
      ['적자 확률 · 범위', '노트북 6장 모델 예측'],
      ['최악 · 최적', '모델 기준 하위 · 상위 10%'],
      ['불황 점검', '업계가 실제 겪은 충격 재적용', `출처 확인 업황 사건 ${nEvents}건 포함`],
    ]))}
    ${keys(['Dart-B HR 학술제 MVP', '아이콘 Lucide (ISC)', '글꼴 Pretendard (OFL)'])}
  </article>`;
}

// ---------------------------------------------------------------- 라우팅
function route() {
  if (!CTX) return;
  const h = location.hash.replace(/^#/, '') || '/';
  const m = h.match(/^\/f\/(\d+)(\/(range|link|risk))?$/);
  try {
    if (m && CTX.firms.has(m[1])) {
      const id = m[1];
      LAST_FIRM = id;
      if (!m[3]) viewSummary(id);
      else if (m[3] === 'range') viewRange(id);
      else if (m[3] === 'link') viewLink(id);
      else viewRisk(id);
    } else if (h === '/about') viewAbout();
    else viewFind();
  } catch (err) {
    console.error(err);
    $view.innerHTML = `<div class="error-box callout neutral">${icon('circle-alert', 18)}<span>이 화면을 그리는 중 문제가 생겼습니다. <a href="#/">처음으로</a> 돌아가 다시 시도해 주세요.</span></div>`;
  }
  window.scrollTo(0, 0);
  $view.focus({ preventScroll: true });
  // 화면 전환: 섹션이 위에서부터 차례로 떠오름
  $view.classList.remove('view-in'); void $view.offsetWidth; $view.classList.add('view-in');
}

(async function start() {
  try {
    await loadAll();
  } catch (err) {
    console.error(err);
    $view.innerHTML = `<div class="error-box callout neutral">${icon('circle-alert', 18)}<span>데이터를 불러오지 못했습니다(${esc(err.message)}). 인터넷 연결을 확인하고 다시 불러와 주세요.</span></div>
      <button class="btn" type="button" style="margin-top:12px" onclick="location.reload()">다시 불러오기</button>`;
    return;
  }
  window.addEventListener('hashchange', route);
  route();
})();
