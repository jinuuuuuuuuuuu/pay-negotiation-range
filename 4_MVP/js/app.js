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
  if (a >= 1e12) return `${s}${(a / 1e12).toFixed(2).replace(/\.?0+$/, '')}조 원`;
  if (a >= 1e8) return `${s}${Math.round(a / 1e8).toLocaleString('ko-KR')}억 원`;
  if (a >= 1e4) return `${s}${Math.round(a / 1e4).toLocaleString('ko-KR')}만 원`;
  return `${s}${Math.round(a).toLocaleString('ko-KR')}원`;
}
const man = (x) => (isNum(x) ? `${Math.round(x / 1e4).toLocaleString('ko-KR')}만 원` : '—');
const man0 = (x) => (isNum(x) ? `${Math.round(x / 1e4).toLocaleString('ko-KR')}만` : '—');
// formula.py가 만든 문구의 '업종'을 화면에서는 '업계'로 (계산·결과 파일은 그대로)
const u = (s) => String(s ?? '').replace(/업종/g, '업계');

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
const SCN_NAME = { 평상시: '불황이 없을 때', '모델 중앙(P50)': '모델 예측: 보통 시나리오', '모델 나쁜 쪽(P10)': '모델 예측: 최악의 시나리오' };
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
      link: { alpha: null },
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
    ${about ? `<a class="icon-btn" href="#/about" aria-label="근거와 한계">${icon('info', 22)}</a>` : '<span class="spacer"></span>'}`;
  document.querySelector('meta[name="theme-color"]').content = dark ? '#1F1F1F' : '#F3F3F2';
}
function setTabs(id, active) {
  if (!id) { $tabs.hidden = true; $view.classList.add('no-tabs'); return; }
  $tabs.hidden = false; $view.classList.remove('no-tabs');
  const t = [['', '요약', 'house'], ['/range', '협상 구간', 'scale'], ['/link', '이익연동', 'coins'], ['/risk', '미래 위험', 'cloud-lightning']];
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

// 업계 대비 임금 위치: x = 회사(1인당 급여 높은 순), y = 1인당 급여
function wageChart(f) {
  const peers = peersOf(f.id).filter((p) => isNum(p.w));
  if (!peers.length || !isNum(f.w)) return { svg: '<p class="note">비교할 업계 회사가 없어 그래프를 그릴 수 없습니다.</p>', rank: null, n: 0 };
  const items = [...peers.map((p) => ({ w: p.w, us: false })), { w: f.w, us: true }].sort((a, b) => b.w - a.w);
  const n = items.length, rank = items.findIndex((x) => x.us) + 1;
  const H = 210, T = 30, B = 26, L = 2, R = 2, ph = H - T - B;
  const max = niceMax(items[0].w * 1.04);
  const step = (W - L - R) / n, bw = Math.max(step * 0.66, 4);
  const py = (v) => T + ph * (1 - v / max);
  const med = isNum(f.peer_median_10k) ? f.peer_median_10k * 1e4 : NaN;
  let bars = '';
  items.forEach((it, i) => {
    const x = L + i * step + (step - bw) / 2, y = py(it.w);
    bars += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${(T + ph - y).toFixed(1)}" rx="2.5" class="${it.us ? 'bar-us' : 'bar'}"/>`;
  });
  const ui = rank - 1, ux = L + ui * step + step / 2, uy = py(f.w);
  let medEl = '';
  if (isNum(med)) {
    const my = py(med), leftSide = ui > n / 2;
    medEl = `<line x1="${L}" x2="${W - R}" y1="${my.toFixed(1)}" y2="${my.toFixed(1)}" class="ln-ind"/>${tx(leftSide ? L + 2 : W - R - 2, my - 6, `업계 중앙 ${man0(med)}`, 'cl-m', leftSide ? 'start' : 'end')}`;
  }
  const lab = tx(clamp(ux, 40, W - 40), uy - 9, `우리 ${man0(f.w)}`, 'cl-b', 'middle');
  const axis = `<line x1="${L}" x2="${W - R}" y1="${T + ph}" y2="${T + ph}" class="ax"/>${tx(L, H - 6, '← 급여 높은 회사', 'cl')}${tx(W - R, H - 6, '급여 낮은 회사 →', 'cl', 'end')}`;
  return {
    svg: `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="비교군 ${n - 1}곳과 우리 회사의 1인당 급여, 높은 순. 우리 회사 ${n}곳 중 ${rank}위">${bars}${medEl}${axis}${lab}</svg>`,
    rank, n,
  };
}

// 협상 구간: x = 기본급 인상률, y = 인상 비용 ÷ 영업이익(3년 평균 기준, 기본급 인상분)
function rangeChart(f, rng, offers = null, compact = false) {
  const cb = CTX.C.OVERHEAD_C_BASE, showMax = CTX.C.RANGE_UPPER_SHOW_MAX;
  const g = rng['하한'], up = rng['상한'];
  if (!isNum(g)) return '';
  const ops = f.S_avg > 0 ? f.OP_avg / f.S_avg : NaN, pops = f.peer_ops;
  const hasUs = isNum(ops) && ops > 0, hasInd = isNum(pops) && pops > 0;
  const yUs = (r) => (r * (1 + cb) / ops) * 100;
  const yInd = hasInd ? (g * (1 + cb) / pops) * 100 : NaN;
  const xc = [0.06, g * 1.6];
  if (isNum(up)) xc.push(Math.min(up, 0.12) * 1.2);
  if (offers) xc.push(offers.union * 1.15, offers.company * 1.15);
  const M = Math.min(Math.ceil(Math.max(...xc) * 100) / 100, 0.3);
  const yc = [3];
  if (hasInd) yc.push(yInd * 1.45);
  if (hasUs) yc.push(yUs(isNum(up) && up > 0 ? Math.min(up, M) : g) * 1.25);
  if (hasUs && offers) yc.push(yUs(Math.max(offers.union, offers.company)) * 1.1);
  const yMax = niceMax(Math.min(Math.max(...yc), 150));
  const H = compact ? 214 : 236, T = 34, B = 30, L = 34, R = 10, pw = W - L - R, ph = H - T - B;
  const px = (x) => L + (clamp(x, 0, M) / M) * pw;
  const py = (y) => T + ph * (1 - clamp(y, 0, yMax) / yMax);
  let s = `<defs><clipPath id="clipR${compact ? 'c' : 'f'}"><rect x="${L}" y="${T}" width="${pw}" height="${ph}"/></clipPath></defs>`;
  // 격자와 y 눈금
  for (const v of [0, yMax / 2, yMax]) {
    s += `<line x1="${L}" x2="${W - R}" y1="${py(v).toFixed(1)}" y2="${py(v).toFixed(1)}" class="${v === 0 ? 'ax' : 'grid'}"/>`;
    s += tx(L - 5, py(v) + 4, `${+v.toFixed(1)}%`, 'cl', 'end');
  }
  // 협상 구간 면
  if (isNum(up)) {
    const a = Math.min(g, up), b = Math.max(g, up);
    s += `<rect x="${px(a).toFixed(1)}" y="${T}" width="${Math.max(px(b) - px(a), 1.5).toFixed(1)}" height="${ph}" class="${up >= g ? 'zone' : 'zone-bad'}"/>`;
  }
  // 업계 부담선
  if (hasInd) {
    s += `<line x1="${L}" x2="${W - R}" y1="${py(yInd).toFixed(1)}" y2="${py(yInd).toFixed(1)}" class="ln-ind"/>`;
    s += tx(L + 4, py(yInd) - 6, `업계 부담 ${yInd.toFixed(1)}%`, 'cl-m', 'start');
  }
  // 우리 회사 부담선 (이름은 범례에서)
  if (hasUs) {
    s += `<line x1="${px(0)}" y1="${py(0)}" x2="${px(M).toFixed(1)}" y2="${(T + ph * (1 - yUs(M) / yMax)).toFixed(1)}" class="ln-us" clip-path="url(#clipR${compact ? 'c' : 'f'})"/>`;
  }
  // 하한·상한 세로선과 이름표
  const xg = px(g);
  s += `<line x1="${xg.toFixed(1)}" x2="${xg.toFixed(1)}" y1="${T}" y2="${T + ph}" class="vl"/>`;
  let upX = null, upLab = '';
  if (isNum(up)) {
    if (up > M || up > showMax) { upX = up > M ? W - R : px(up); upLab = `상한 ${Math.round(showMax * 100)}% 초과`; } else { upX = px(up); upLab = `상한 ${pct(up)}`; }
    s += `<line x1="${upX.toFixed(1)}" x2="${upX.toFixed(1)}" y1="${T}" y2="${T + ph}" class="vl dash"/>`;
  }
  const near = upX !== null && Math.abs(upX - xg) < 64;
  const gLeft = upX !== null && xg < upX;
  s += tx(clamp(xg, L + 20, W - R - 20), T - 10, `하한 ${pct(g)}`, 'cl-b', near ? (gLeft ? 'end' : 'start') : 'middle');
  if (upX !== null) s += tx(clamp(upX, L + 20, W - R - 2), T - 10, upLab, 'cl-b', near ? (gLeft ? 'start' : 'end') : (upX > W - R - 40 ? 'end' : 'middle'));
  // 교점 (상한이 계산된 경우)
  if (hasUs && hasInd && rng['상한 상태'] === '계산' && up <= M) s += `<circle cx="${px(up).toFixed(1)}" cy="${py(yInd).toFixed(1)}" r="4" class="pt-x"/>`;
  // 노조안·회사안 점
  if (offers && !compact) {
    const pts = [['회사', offers.company, 'pt-co'], ['노조', offers.union, 'pt-un']];
    const xs = pts.map(([, v]) => px(v));
    const close = Math.abs(xs[0] - xs[1]) < 56;
    pts.forEach(([who, v, cls], i) => {
      const x = px(v), y = hasUs ? py(yUs(v)) : py(0);
      const anchor = close ? (xs[i] <= xs[1 - i] ? 'end' : 'start') : 'middle';
      const dx = close ? (anchor === 'end' ? -8 : 8) : 0;
      s += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="6.5" class="${cls}"/>`;
      s += tx(clamp(x + dx, L + 24, W - R - 4), clamp(y - 12, T + 10, T + ph - 6), `${who} ${pct(v)}`, 'cl-b', anchor);
    });
  }
  // x 눈금
  for (const v of [0, M / 2, M]) s += tx(px(v), H - 10, `${+(v * 100).toFixed(1)}%`, 'cl', v === 0 ? 'start' : v === M ? 'end' : 'middle');
  s += tx(L + pw / 2, H - 10, '', 'cl');
  const aria = `협상 구간 그래프. 하한 ${pct(g)}${isNum(up) ? `, 상한 ${rng['상한 표시']}` : ''}${offers ? `, 노조안 ${pct(offers.union)}, 회사안 ${pct(offers.company)}` : ''}`;
  const legend = `<div class="legend2">
      ${hasUs ? '<span><i class="sw-us"></i>우리 회사: 인상률별로 영업이익에서 나가는 비중</span>' : ''}
      ${hasInd ? '<span><i class="sw-ind"></i>업계 부담: 비교군이 업계 인상률만큼 올릴 때의 비중</span>' : ''}
      ${isNum(up) ? `<span><i class="sw-zone${up >= g ? '' : ' bad'}"></i>${up >= g ? '협상 구간 (하한 ~ 상한)' : '업계만큼 올리면 부담이 업계보다 커지는 구간'}</span>` : ''}
    </div>
    <p class="axis-note">가로: 기본급 인상률 · 세로: 영업이익 중 인상 비용 (기본급 인상분, 3년 평균 이익 기준)</p>`;
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(aria)}">${s}</svg>${legend}`;
}

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
      <p>회사를 고르면 업계 비교군 20곳을 기준으로 협상 구간과 그 근거를 보여 드립니다.</p>
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
      <a class="link-row" href="#/about">${icon('info', 20)}<span>데이터와 계산의 근거·한계</span></a>
      <p class="note">DART 공시 ${CTX.list.length.toLocaleString('ko-KR')}곳 · 진단 구간 ${CTX.meta.start}~${CTX.meta.end}년</p>
    </div>`;
  const $q = document.getElementById('q');
  const $res = document.getElementById('res');
  const run = () => {
    const raw = $q.value.trim();
    const q = raw.replace(/\s+/g, '').toLowerCase();
    if (!q) { $res.innerHTML = ''; return; }
    const hit = CTX.list.filter((f) => f.key.includes(q) || (f.code && f.code.startsWith(q)));
    hit.sort((a, b) => (b.key.startsWith(q) - a.key.startsWith(q)) || (b.size - a.size));
    if (!hit.length) { $res.innerHTML = `<li class="empty">'${esc(raw)}'와 맞는 회사가 없습니다. 상장사 이름의 일부나 6자리 종목코드로 찾아 보세요.</li>`; return; }
    $res.innerHTML = hit.slice(0, 30).map((f) => {
      const i = f.name.replace(/\s+/g, '').toLowerCase().indexOf(q);
      const nm = i >= 0 && !/\s/.test(f.name) ? `${esc(f.name.slice(0, i))}<mark>${esc(f.name.slice(i, i + q.length))}</mark>${esc(f.name.slice(i + q.length))}` : esc(f.name);
      return `<li><a class="result" href="#/f/${f.id}"><span class="grow"><span class="name">${nm}</span><span class="meta">${esc(f.ind)}${f.code ? ` · ${f.code}` : ''}</span></span>${icon('chevron-right', 20)}</a></li>`;
    }).join('') + (hit.length > 30 ? `<li class="empty">${hit.length - 30}곳 더 있습니다. 이름을 더 입력해 좁혀 주세요.</li>` : '');
  };
  $q.addEventListener('input', run);
  $view.querySelectorAll('[data-ex]').forEach((b) => b.addEventListener('click', () => { $q.value = b.dataset.ex; run(); }));
}

// ---------------------------------------------------------------- 화면: 요약·진단
function heroCard(f, rng) {
  const gap = isNum(f.wage_gap_pct) ? `업계 중앙 대비 ${signed(f.wage_gap_pct)}` : '비교할 업계 회사가 부족함';
  const capSub = f.capacity === '여력 제약' ? u(f.capacity_reason || '') : `영업이익률 ${pctRaw(f.opm_pct)} · 업계 ${pctRaw(f.opm_ind_pct)}`;
  let line;
  const state = rng['상한 상태'];
  if (state === '비교군 인상률 없음') {
    line = `<div class="rangeline hold"><div class="k">협상 구간</div><div class="v">계산할 수 없음</div><div class="s">비교군(같은 업계 20곳)을 만들 수 없는 회사입니다</div></div>`;
  } else if (state === CTX.C.RANGE_HOLD_TEXT) {
    line = `<div class="rangeline"><div class="k">협상 구간</div><div class="v">하한 ${pct(rng['하한'])}</div><div class="s">${esc(state)}</div></div>`;
  } else {
    line = `<div class="rangeline"><div class="k">협상 구간</div><div class="v">하한 ${pct(rng['하한'])} ~ 상한 ${esc(rng['상한 표시'])}</div><div class="s">${esc(rng['구간 해석'])}</div></div>`;
  }
  return `<section class="hero">
    <h2 class="co">${esc(f.name)}</h2>
    <p class="ind">${esc(f.ind2_name || '')}${f.stock_code ? ` · ${f.stock_code}` : ''}${f.market ? ` · ${esc(f.market)}` : ''}</p>
    <div class="axes">
      <div class="axis"><div class="k">업계 대비 임금 위치</div><div class="v">${esc(f.wage_pos || '—')}</div><div class="s">${gap}</div></div>
      <div class="axis"><div class="k">업계 대비 이익률</div><div class="v">${esc(CAP_LABEL[f.capacity] || f.capacity || '—')}</div><div class="s">${esc(capSub)}</div></div>
    </div>
    ${line}
  </section>`;
}

function diagnosis(f, rng, wc) {
  const wageW = { '임금 높음': '업계보다 높고', '임금 보통': '업계 수준이고', '임금 낮음': '업계보다 낮고' }[f.wage_pos] || '업계와 비교할 수 없고';
  const capW = { '여력 있음': '업계보다 높은 회사', '여력 보통': '업계보다 낮은 회사', '여력 제약': '적자나 이자 부담으로 제약된 회사', '판정 불가': '판단하기 어려운 회사' }[f.capacity] || '판단하기 어려운 회사';
  const one = `임금은 ${wageW}, 이익률은 ${capW}입니다.`;
  const b1 = isNum(f.wage_gap_pct)
    ? `1인당 급여 ${isNum(f.wage_10k) ? Math.round(f.wage_10k).toLocaleString('ko-KR') : '—'}만 원, 업계 중앙보다 ${Math.abs(f.wage_gap_pct).toFixed(1)}% ${f.wage_gap_pct >= 0 ? '높음' : '낮음'}${wc.rank ? ` (${wc.n}곳 중 ${wc.rank}위)` : ''}`
    : `1인당 급여 ${isNum(f.wage_10k) ? Math.round(f.wage_10k).toLocaleString('ko-KR') : '—'}만 원, 비교할 업계 회사가 부족함`;
  const b2 = f.capacity === '여력 제약'
    ? `3년 영업이익률 ${pctRaw(f.opm_pct)}, ${u(f.capacity_reason || '제약')}`
    : `3년 영업이익률 ${pctRaw(f.opm_pct)}, 업계 ${pctRaw(f.opm_ind_pct)}`;
  const st0 = rng['상한 상태'];
  const b3 = st0 === '비교군 인상률 없음' ? '협상 구간을 계산할 수 없음 (업계 인상률을 직접 넣으면 계산)'
    : st0 === CTX.C.RANGE_HOLD_TEXT ? `업계 인상률(하한) ${pct(rng['하한'])}, 업계 적자로 상한은 산출 보류`
      : `협상 구간 ${pct(rng['하한'])} ~ ${rng['상한 표시']}: ${rng['구간 해석']}`;
  return `<p class="one">${esc(one)}</p><ul class="bul"><li>${esc(b1)}</li><li>${esc(b2)}</li><li>${esc(b3)}</li></ul>`;
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
  const hasRange = rng['상한 상태'] !== '비교군 인상률 없음';
  $view.innerHTML = `
    ${heroCard(f, rng)}
    <section class="section">
      <h2>한 줄 진단</h2>
      <div class="panel diag">${diagnosis(f, rng, wc)}</div>
    </section>
    ${hasRange ? `<section class="section">
      <h2>협상 구간</h2>
      <div class="panel">${rangeChart(f, rng, null, true)}
        <a class="btn" href="#/f/${id}/range" style="margin-top:14px">노조안·회사안 넣어 보기 ${icon('chevron-right', 20)}</a>
      </div>
    </section>` : ''}
    <section class="section">
      <h2>업계 대비 임금 위치</h2>
      <p class="lead">같은 업계에서 매출·1인당 자산이 비슷한 회사 20곳과 1인당 급여(3년)를 비교했습니다.</p>
      <div class="panel">
        ${wc.svg}
        <hr class="divider">
        <dl class="kv">
          <dt>우리 1인당 급여(3년)</dt><dd class="num">${isNum(f.wage_10k) ? `${Math.round(f.wage_10k).toLocaleString('ko-KR')}만 원` : '—'}</dd>
          <dt>업계 중앙</dt><dd class="num">${isNum(f.peer_median_10k) ? `${Math.round(f.peer_median_10k).toLocaleString('ko-KR')}만 원` : '—'}</dd>
          <dt>업계 중앙 대비</dt><dd class="num">${signed(f.wage_gap_pct)}</dd>
          <dt>순위</dt><dd class="num">${wc.rank ? `${wc.n}곳 중 ${wc.rank}위` : '—'}</dd>
        </dl>
        ${f.wage_pos === '임금 낮음' ? `<div class="callout" style="margin-top:14px">${icon('users', 18)}<span>업계 대비 임금 위치 하위 20% 회사들은 정규직 자발적 이직률이 상위 20%보다 약 5%p 높았습니다(17.8% vs 12.7%, WPS 분석). 같은 회사가 임금을 올렸을 때 이직이 줄어드는지는 확인되지 않았습니다.</span></div>` : ''}
        ${f.peer_warn ? `<p class="note" style="margin-top:10px">주의: ${esc(u(f.peer_warn))}</p>` : ''}
      </div>
    </section>
    <section class="section">
      <h2>업계 대비 이익률</h2>
      <p class="lead">3년 합산 영업이익률을 같은 업계의 중앙값과 비교했습니다.</p>
      <div class="panel">
        <div class="bars2">
          <div class="b"><span>우리 회사</span>${bar(opm, '')}<span class="val num">${pctRaw(opm)}</span></div>
          <div class="b"><span>업계 중앙</span>${bar(ind, 'ind')}<span class="val num">${pctRaw(ind)}</span></div>
        </div>
        <hr class="divider">
        <dl class="kv">
          <dt>판정</dt><dd>${esc(CAP_LABEL[f.capacity] || '—')}</dd>
          <dt>인건비율 (급여÷매출)</dt><dd class="num">${pctRaw(f.labor_ratio_pct)} <span class="muted small">업계 ${pctRaw(f.peer_labor_ratio_pct)}</span></dd>
          <dt>영업이익률 평소 변동</dt><dd class="num">${isNum(f.opm_sd_pctp) ? `${f.opm_sd_pctp.toFixed(1)}%p` : '<span class="muted small">자료 부족</span>'}</dd>
        </dl>
        ${f.cf_flag ? `<p class="note" style="margin-top:10px">${esc(u(f.cf_flag))}</p>` : ''}
        ${f.pay_check ? `<p class="note" style="margin-top:6px">${esc(u(f.pay_check))}</p>` : ''}
      </div>
    </section>
    ${peers.length ? `<section class="section">
      <details class="more panel">
        <summary>비교군 20곳 보기 (급여 높은 순) ${icon('chevron-right', 18)}</summary>
        <ul class="peers-list">${peers.map((p, i) => `<li><span><span class="rk">${i + 1}</span>${esc(p.name)}${p.ind2 === f.ind2 ? '' : '<span class="same">다른 업계 분류</span>'}</span><span class="num">${man(p.w)}</span></li>`).join('')}</ul>
        <p class="note" style="margin-top:8px">금액은 1인당 급여(3년, 급여총액÷직원수)입니다.</p>
      </details>
    </section>` : ''}`;
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
    $view.innerHTML = `<section class="section"><h2>인상안 협상 구간</h2>
      <div class="callout neutral">${icon('circle-alert', 18)}<span>이 회사는 비교군(같은 업계에서 비슷한 회사 20곳)을 만들 수 없어 업계 인상률을 계산할 수 없습니다. 업계 인상률을 직접 넣으면 구간을 계산합니다.</span></div>
      <button class="btn" type="button" id="ovon" style="margin-top:12px">업계 인상률 직접 넣기</button></section>`;
    document.getElementById('ovon').addEventListener('click', () => { S.override = 0.04; viewRange(id); });
    return;
  }
  const ov = S.override;
  $view.innerHTML = `
    <section class="section" style="margin-top:12px">
      <h2>인상안 협상 구간</h2>
      <p class="lead">하한은 노측이, 상한은 사측이 내세울 수 있는 근거입니다. 노조안·회사안은 그래프 위의 점입니다.</p>
      <div class="panel" id="chartbox"></div>
      <details class="more panel">
        <summary>하한과 상한은 어떻게 정하나 ${icon('chevron-right', 18)}</summary>
        <div class="note stack">
          <p><strong>하한 = 업계 인상률.</strong> 비교군 20곳의 최근 3년 1인당 급여 연 증가율 중앙값입니다. 이보다 낮게 올리면 업계 대비 임금 위치가 내려갑니다. 임금 위치가 낮은 회사일수록 자발적 이직이 많았습니다(WPS 분석).</p>
          <p><strong>상한 = 업계와 같은 부담 수준.</strong> 그래프의 검은 선(우리 회사 부담)이 점선(업계 부담)과 만나는 인상률입니다. 우리 회사의 이익이 급여에 비해 업계보다 크면 선이 완만해져 상한이 하한보다 높아지고, 작으면 낮아집니다. 감당 한도가 아니라 업계 기준으로 맞춘 선입니다.</p>
          <p>1인당 급여 증가율에는 성과급·승진·인력 구성 변화가 섞여 있어 기본급 인상률 자체와는 다를 수 있습니다.</p>
        </div>
      </details>
    </section>
    <section class="section">
      <h2>두 안 넣기</h2>
      <div class="offer"><div class="offer-head"><h3><span class="who union"></span>노조안</h3></div>
        <div class="fields">${stepper('ub', S.union.base, { label: '기본급 인상률' })}${stepper('ux', S.union.bonus, { label: '일시 성과급(급여 대비)' })}</div></div>
      <div class="offer"><div class="offer-head"><h3><span class="who"></span>회사안</h3></div>
        <div class="fields">${stepper('cb', S.company.base, { label: '기본급 인상률' })}${stepper('cx', S.company.bonus, { label: '일시 성과급(급여 대비)' })}</div></div>
      <details class="more panel">
        <summary>두 안에 같이 적용할 가정 ${icon('chevron-right', 18)}</summary>
        ${sw('ov', ov !== null, '업계 인상률 직접 입력', '켜면 하한·상한을 이 값으로 다시 계산')}
        <div id="ovf" ${ov === null ? 'hidden' : ''}>${stepper('ov', ov ?? (isNum(f.peer_growth) ? f.peer_growth : 0.04), { label: '업계 인상률', step: 0.1, max: 30 })}</div>
        <hr class="divider">
        <div class="fields">${stepper('hc', S.headcount, { label: '인원 증감', min: -50, max: 50 })}${stepper('sg', S.sales, { label: '매출 증가율', min: -80, max: 100 })}</div>
        <p class="note" style="margin-top:8px">새로 뽑는 사람의 급여는 지금 1인당 평균, 늘어난 매출에도 지금 영업이익률이 그대로라고 가정합니다. 불황이 오면 어떻게 되는지는 미래 위험 탭에서 봅니다.</p>
      </details>
    </section>
    <section class="section">
      <h2>두 안 비교</h2>
      <div class="panel" id="cmpbox"></div>
      <div class="row" style="margin-top:12px;gap:10px">
        <a class="btn secondary half" href="#/f/${id}/link">${icon('coins', 18)}이익연동이면</a>
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
    if (state === CTX.C.RANGE_HOLD_TEXT) interp = `<div class="callout neutral">${icon('circle-alert', 18)}<span><strong>업계 적자로 인한 상한 산출 보류.</strong> 비교군 대부분이 적자라 "업계만큼의 부담"을 정할 수 없습니다. 하한(업계 인상률)만 참고하고, 고정 인상보다 이익연동 전환을 함께 검토해 보세요.</span></div>`;
    else if (state === '3년 합산 영업적자') interp = `<div class="callout">${icon('circle-alert', 18)}<span><strong>3년 합산 영업적자라 상한이 0%입니다.</strong> 이익이 없어 우리 회사 부담선을 그릴 수 없습니다. 고정 인상 대신 이익연동 전환을 검토해 보세요.</span></div>`;
    else interp = `<div class="callout">${icon('scale', 18)}<span>${esc(rng['구간 해석'])}${state === '적자 전환 직전에서 제한' ? ' (마지막 해 영업이익을 다 쓰는 선에서 상한을 멈췄습니다)' : ''}${rng['상한'] > CTX.C.RANGE_UPPER_SHOW_MAX ? '. 상한이 10%를 넘어 숫자 대신 "10% 초과"로 표시합니다' : ''}</span></div>`;
    const pos = (k) => `<span class="badge ${posClass(R('구간 위치')[k])}"><span class="dot"></span>${esc(R('구간 위치')[k])}</span>`;
    document.getElementById('chartbox').innerHTML = `${rangeChart(f, rng, { union: S.union.base, company: S.company.base })}
      <div class="pos-row"><div><span class="k">노조안</span>${pos('노조안')}</div><div><span class="k">회사안</span>${pos('회사안')}</div></div>
      <div style="margin-top:12px">${interp}</div>`;
    const yes = (v) => (v ? '<span class="badge above">예</span>' : '아니요');
    const rank = (v) => (isNum(v) ? `상위 ${Math.max(1, Math.round((1 - v) * 100))}%` : '—');
    document.getElementById('cmpbox').innerHTML = `
      <table class="cmp">
        <thead><tr><th></th><th>노조안</th><th>회사안</th></tr></thead>
        <tbody>
          <tr><th scope="row">회사 부담 증가 (1년)</th><td>${won(R('회사 부담 증가(1년)')['노조안'])}</td><td>${won(R('회사 부담 증가(1년)')['회사안'])}</td></tr>
          <tr><th scope="row">3년 누적 부담</th><td>${won(R('3년 누적 부담(인원·기본급 유지 + 성과급 1회)')['노조안'])}</td><td>${won(R('3년 누적 부담(인원·기본급 유지 + 성과급 1회)')['회사안'])}</td></tr>
          <tr><th scope="row">비용 ÷ 영업이익</th><td>${pctRaw(R('비용÷영업이익(%)')['노조안'])}</td><td>${pctRaw(R('비용÷영업이익(%)')['회사안'])}</td></tr>
          <tr><th scope="row">내년 영업이익률</th><td>${pctRaw(R('내년 영업이익률(%)')['노조안'])}</td><td>${pctRaw(R('내년 영업이익률(%)')['회사안'])}</td></tr>
          <tr><th scope="row">내년 업계 대비 임금</th><td>${signed(R('내년 예상 임금 차이(%)')['노조안'])}<span class="sub">${rank(R('내년 예상 순위')['노조안'])}</span></td><td>${signed(R('내년 예상 임금 차이(%)')['회사안'])}<span class="sub">${rank(R('내년 예상 순위')['회사안'])}</span></td></tr>
          <tr><th scope="row">지급 때문에 적자 전환</th><td>${yes(R('지급 때문에 적자 전환')['노조안'])}</td><td>${yes(R('지급 때문에 적자 전환')['회사안'])}</td></tr>
        </tbody>
      </table>
      <p class="note" style="margin-top:10px">두 안의 1년 부담 차이 <strong>${won(R('회사 부담 증가(1년)')['차이(노조안 − 회사안)'])}</strong>. 기본급 인상에는 4대보험·퇴직금(약 18.3%), 일시 성과급에는 4대보험(10%) 부담을 더했습니다. 이 표는 성과급과 마지막 해 영업이익까지 넣은 값이라 그래프(기본급 인상분, 3년 평균 이익)와 숫자가 다를 수 있습니다. 내년 업계 대비 임금은 비교군도 업계 인상률(${pct(R('비교군 인상률 가정')['노조안'])})만큼 오른다고 본 값입니다.</p>`;
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

// ---------------------------------------------------------------- 화면: 이익연동 전환
function viewLink(id) {
  const f = CTX.firms.get(id);
  const S = st(id);
  setTop({ title: f.name, back: '#/' });
  setTabs(id, '/link');
  const aStar = f.alpha_star;
  const a0 = S.link.alpha ?? (isNum(aStar) ? aStar : 0.05);
  const maxA = Math.max(0.3, isNum(aStar) ? aStar * 2.5 : 0.3);
  $view.innerHTML = `
    <section class="section" style="margin-top:12px">
      <h2>이익연동 전환</h2>
      <p class="lead">급여의 5%를 고정으로 주던 성과급을 "영업이익의 몇 %"로 바꾸면 어떻게 되는지 봅니다. 기준은 진단과 같은 3년 연평균입니다.</p>
      ${isNum(aStar) ? `<div class="callout">${icon('coins', 18)}<span>시작값 <strong>영업이익의 ${pct(aStar)}</strong>를 주면 지금의 고정 지급(급여 5%)과 같은 금액입니다.</span></div>`
        : `<div class="callout neutral">${icon('circle-alert', 18)}<span>3년 합산 영업적자라 시작값을 계산하지 않습니다. 연동 방식이면 이익이 날 때까지 지급액이 0원입니다.</span></div>`}
    </section>
    <section class="section">
      <div class="panel">
        <div class="row between"><label for="alpha" class="t" style="font-weight:600">영업이익 대비 지급 비율</label><strong class="num" id="alv">${pct(a0)}</strong></div>
        <input class="slider" id="alpha" type="range" min="0" max="${(maxA * 100).toFixed(1)}" step="0.1" value="${(a0 * 100).toFixed(1)}">
        ${isNum(aStar) ? `<button class="chip" id="reset" type="button">시작값 ${pct(aStar)}로</button>` : ''}
      </div>
    </section>
    <section class="section">
      <h2>고정 vs 연동</h2>
      <div class="panel" id="lres"></div>
      <p class="note" style="margin-top:10px">흑자일 때 연동 방식의 회사 부담 ÷ 영업이익은 비율 × 1.1로 어느 회사나 같습니다. 회사마다 달라지는 것은 직원이 받는 급여 대비 지급률입니다. 성과급이 생산성을 올린다는 근거는 이번 분석에서 찾지 못했습니다(성과급은 성과를 뒤따라 지급됨, WPS 분석).</p>
      <a class="btn secondary" href="#/f/${id}/risk" style="margin-top:12px">${icon('cloud-lightning', 18)}불황이 오면 연동 지급은?</a>
    </section>`;
  const alpha = () => S.link.alpha ?? (isNum(aStar) ? aStar : 0.05);
  const draw = () => {
    const r = E.profitLinkPlan(CTX, id, { alpha: alpha() });
    document.getElementById('alv').textContent = pct(alpha());
    const ratio = r['연동 ÷ 고정'];
    document.getElementById('lres').innerHTML = `
      <table class="cmp">
        <thead><tr><th></th><th>고정 (급여 5%)</th><th>연동</th></tr></thead>
        <tbody>
          <tr><th scope="row">1년 지급 총액</th><td>${won(r['고정 지급(급여 대비 rate)'])}</td><td>${won(r['연동 지급'])}</td></tr>
          <tr><th scope="row">1인당</th><td>${man(r['1인당 고정 지급'])}</td><td>${man(r['1인당 연동 지급'])}</td></tr>
          <tr><th scope="row">회사 부담 ÷ 영업이익</th><td>${pctRaw(r['고정 부담 ÷ 영업이익(%)'])}</td><td>${pctRaw(r['연동 부담 ÷ 영업이익(%)'])}</td></tr>
          <tr><th scope="row">급여 대비 지급률</th><td>5.0%</td><td>${pctRaw(r['급여 대비 지급률(%)'])}</td></tr>
        </tbody>
      </table>
      <p class="note" style="margin-top:10px">${r['0원 지급'] ? '<strong>영업이익이 0 이하라 연동 지급은 0원입니다.</strong> ' : ''}연동 ÷ 고정 = <strong>${isNum(ratio) ? `${ratio.toFixed(2)}배` : '—'}</strong> · 영업이익(3년 연평균) ${won(r['영업이익(3년 연평균)'])}</p>`;
  };
  const $a = document.getElementById('alpha');
  $a.addEventListener('input', () => { S.link.alpha = Number($a.value) / 100; draw(); });
  const $r = document.getElementById('reset');
  if ($r) $r.addEventListener('click', () => { S.link.alpha = null; $a.value = (aStar * 100).toFixed(1); draw(); });
  draw();
}

// ---------------------------------------------------------------- 화면: 미래 위험
const COMMON_DESC = {
  코로나형: '2020년 코로나19 확산 때 각 업계가 실제로 겪은 영업이익률·매출 변화를 다시 적용합니다.',
  '원자재·금리형': '2022년 원자재 가격 급등과 금리 인상 때 각 업계가 실제로 겪은 변화를 다시 적용합니다.',
};
function scnInfo(name, kind) {
  if (kind === '직접 입력') return { desc: '직접 정한 영업이익률·매출 변화를 적용합니다.', src: [] };
  if (kind === '최악의 해') return { desc: '우리 업계의 영업이익률이 가장 크게 떨어졌던 해의 변화를 다시 적용합니다. 원인이 확인된 사건이 아닐 수 있습니다.', src: [] };
  for (const [k, d] of Object.entries(COMMON_DESC)) if (name.startsWith(k)) return { desc: d, src: [] };
  const row = (CTX.catalog || []).find((r) => name.startsWith(`${r['사건명']} (${r['연도']})`));
  if (!row) return { desc: '', src: [] };
  const src = String(row['출처'] || '').split(' | ').filter((x) => /^https?:\/\//.test(x)).slice(0, 2);
  return { desc: u(row['원인근거'] || ''), src, level: row['확인수준'] };
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
    return `<optgroup label="${esc(SCN_KIND[gname])}">${xs.map((x) => `<option value="${esc(x['경우'])}" ${S.risk.pick === x['경우'] ? 'selected' : ''}>${esc(u(x['경우']))}</option>`).join('')}</optgroup>`;
  }).join('') + `<optgroup label="직접 입력"><option value="직접 입력" ${S.risk.pick === '직접 입력' ? 'selected' : ''}>직접 충격 정하기</option></optgroup>`;

  $view.innerHTML = `
    <section class="section" style="margin-top:12px">
      <h2>미래 위험</h2>
      <p class="lead">회사안(기본급 ${pct(S.company.base)}, 성과급 ${pct(S.company.bonus)})과 이익연동 비율을 그대로 받아 봅니다. <a href="#/f/${id}/range">안 바꾸기</a></p>
      <div class="panel" id="fcbox"></div>
    </section>
    <section class="section">
      <h2>업계 불황 대비 점검</h2>
      <p class="lead">그때 같은 불황이 다시 오면 이 안을 버틸 수 있을까요? 불황을 하나 고르면 그해 우리 업계가 실제로 겪은 변화를 적용합니다.</p>
      <div class="panel">
        <label class="pick-label" for="pick">어떤 불황을 볼까요</label>
        <div class="pick">${icon('cloud-lightning', 18)}<select id="pick">${opts}</select>${icon('chevron-right', 18, 'pick-chev')}</div>
        <div id="cuf" ${S.risk.pick === '직접 입력' ? '' : 'hidden'} style="margin-top:12px"><div class="fields">${stepper('dm', S.risk.dm, { label: '영업이익률 변화(%p)', min: -50, max: 20 })}${stepper('dr', S.risk.dr, { label: '매출 변화', min: -90, max: 50, step: 1 })}</div></div>
        <div class="seg" role="group" aria-label="충격 크기" style="margin-top:14px">
          <button type="button" data-sev="중앙" aria-pressed="${S.risk.severity === '중앙'}">보통 타격</button>
          <button type="button" data-sev="하위25" aria-pressed="${S.risk.severity === '하위25'}">큰 타격</button>
        </div>
        <p class="note" style="margin-top:6px">보통 타격은 그해 업계 회사들의 중간 수준, 큰 타격은 하위 25% 회사만큼 맞았다고 봅니다.</p>
        ${sw('ws', S.risk.withSales, '매출 감소도 함께', '끄면 영업이익률 변화만 적용')}
      </div>
      <div id="warn"></div>
      <div class="panel" id="scnbox" style="margin-top:12px"></div>
      <p class="note" style="margin-top:10px">과거에 실제로 있었던 일을 다시 적용한 것이지 예측이 아닙니다. 업계 중간값(또는 하위 25%)을 적용해 회사별 충격 크기는 반영하지 않습니다.</p>
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
        <p class="note" style="margin-top:8px">최악의 시나리오에서 지급 후 영업이익 <strong>${won(rows[0][1]['지급 후 영업이익'])}</strong>${rows[0][1]['지급 때문에 적자 전환'] ? ', <strong>지급 때문에 적자로 돌아섭니다</strong>' : ''}. 최악·최적은 모델이 보는 하위·상위 10% 경우입니다.</p>`;
    }
    document.getElementById('fcbox').innerHTML = `<div class="prob"><span class="v num">${isNum(p) ? `${Math.round(p * 100)}%` : '—'}</span><span class="muted small">지금 방식대로일 때 다음 해 영업적자 확률</span></div>${body}
      <p class="note" style="margin-top:8px">노트북 6장 모델의 예측입니다. 적자 해를 가려내는 정확도가 높지 않아(AUC 0.66) 참고 지표로만 보세요.</p>`;
  };
  const draw = () => {
    const custom = S.risk.pick === '직접 입력' ? { 이익률: S.risk.dm, 매출: S.risk.dr } : null;
    const t = E.stressTest(CTX, id, { ...plan, severity: S.risk.severity, with_sales: S.risk.withSales, alpha: S.link.alpha ?? null, custom, useForecast: false });
    document.getElementById('warn').innerHTML = t.attrs['기준 연도 경고'] ? `<div class="callout neutral" style="margin-top:12px">${icon('circle-alert', 18)}<span>${esc(t.attrs['기준 연도 경고'])}</span></div>` : '';
    const base = t.rows['평상시'];
    const r = t.rows[S.risk.pick];
    const $box = document.getElementById('scnbox');
    if (!r) { $box.innerHTML = `<p class="note">이 불황에는 우리 업계의 충격 자료가 없어 계산할 수 없습니다. 다른 불황을 골라 주세요.</p>`; return; }
    const info = scnInfo(S.risk.pick, r['종류']);
    const flag = r['지급 때문에 적자 전환'] ? '<span class="badge above">지급 때문에 적자</span>' : r['지급 후 적자'] ? '<span class="badge hold">원래도 적자</span>' : '<span class="badge inside">흑자 유지</span>';
    const shock = isNum(r['영업이익률 변화(%p)']) ? `업계 영업이익률 ${signed(r['영업이익률 변화(%p)'], 1, '%p')}${isNum(r['매출 변화(%)']) && r['매출 변화(%)'] !== 0 ? ` · 매출 ${signed(r['매출 변화(%)'])}` : ''}` : '';
    const v0 = base['지급 후 영업이익률(%)'], v1 = r['지급 후 영업이익률(%)'];
    const lo = Math.min(0, v0, v1) * 1.15 - 0.5, hi = Math.max(0, v0, v1) * 1.15 + 0.5;
    const ratio = (x) => (isNum(x) ? (x === 0 ? '0원' : `${x.toFixed(2)}배`) : '—');
    $box.innerHTML = `
      <div class="scn-head"><div><h3 class="scn-title">${esc(u(S.risk.pick))}</h3><p class="scn-meta">${esc([SCN_KIND[r['종류']] || r['종류'], info.level ? `근거: ${info.level}` : '', u(r['충격 단위'] || '')].filter(Boolean).join(' · '))}</p></div>${flag}</div>
      ${info.desc ? `<p class="scn-desc">${esc(info.desc)}</p>` : ''}
      ${shock ? `<p class="scn-shock">${esc(shock)}</p>` : ''}
      ${info.src.length ? `<p class="scn-src">${info.src.map((s, i) => `<a href="${esc(s)}" target="_blank" rel="noopener">출처 ${i + 1}</a>`).join(' · ')}</p>` : ''}
      <hr class="divider">
      <p class="small" style="font-weight:600">회사안을 지급한 뒤 내년 영업이익률</p>
      <ul class="sbars">
        <li><span class="lab">${scnName('평상시')}</span>${dbar(v0, lo, hi)}<span class="val num${v0 < 0 ? ' neg' : ''}">${pctRaw(v0)}</span></li>
        <li><span class="lab">이 불황이 오면</span>${dbar(v1, lo, hi)}<span class="val num${v1 < 0 ? ' neg' : ''}">${pctRaw(v1)}</span></li>
      </ul>
      <table class="cmp" style="margin-top:12px">
        <thead><tr><th></th><th>${scnName('평상시')}</th><th>이 불황이 오면</th></tr></thead>
        <tbody>
          <tr><th scope="row">지급 후 영업이익</th><td>${won(base['지급 후 영업이익'])}</td><td class="${r['지급 후 영업이익'] < 0 ? 'neg' : ''}">${won(r['지급 후 영업이익'])}</td></tr>
          <tr><th scope="row">내년 매출</th><td>${won(base['내년 매출'])}</td><td>${won(r['내년 매출'])}</td></tr>
          <tr><th scope="row">이익연동 지급 (고정 대비)</th><td>${ratio(base['이익연동 ÷ 고정'])}</td><td>${ratio(r['이익연동 ÷ 고정'])}</td></tr>
        </tbody>
      </table>`;
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

// ---------------------------------------------------------------- 화면: 근거와 한계
function viewAbout() {
  setTop({ title: '근거와 한계', back: LAST_FIRM ? `#/f/${LAST_FIRM}` : '#/', about: false });
  setTabs(null);
  const nEvents = new Set((CTX.catalog || []).filter((r) => r['확인수준'] !== '원인 미확인').map((r) => r['사건ID'])).size;
  $view.innerHTML = `<article class="prose">
    <h2>데이터</h2>
    <p>DART 공시 패널 2015~2025년에서 직원 10명 이상 비금융 회사 ${CTX.list.length.toLocaleString('ko-KR')}곳을 진단 구간 ${CTX.meta.start}~${CTX.meta.end}년으로 계산했습니다. 급여는 공시 급여총액, 이익은 별도 영업이익입니다. 계산 규칙은 팀의 산술식(formula.py) 하나에서 나오고, 이 앱의 숫자는 그 결과와 같은지 자동으로 검사합니다.</p>
    <h2>협상 구간</h2>
    <ul>
      <li><strong>하한 = 업계 인상률.</strong> 같은 업계에서 매출·1인당 자산이 비슷한 20곳의 최근 3년 1인당 급여 연 증가율 중앙값.</li>
      <li><strong>상한 = 업계와 같은 부담 수준.</strong> 인상 비용 ÷ 영업이익이 비교군과 같아지는 인상률. 감당 한도가 아니라 업계 기준으로 맞춘 선입니다. 10%를 넘으면 "10% 초과", 비교군 대부분이 적자면 "업계 적자로 인한 상한 산출 보류"로 표시합니다.</li>
      <li>노조안·회사안은 사용자가 넣는 안이고, 그래프 위에서 위치를 보여 줍니다.</li>
    </ul>
    <h2>실증 근거 (WPS 사업체패널 2015~2023)</h2>
    <ul>
      <li>임금이 10% 높은 회사는 정규직 자발적 이직률이 0.45%p 낮았습니다. 업계 대비 임금 위치 하위 20%의 이직률은 17.8%, 상위 20%는 12.7%. 같은 회사가 임금을 올렸을 때 이직이 줄어드는지는 확인되지 않았습니다.</li>
      <li>성과급이 생산성을 올린다는 근거는 찾지 못했습니다. 성과급을 준 회사는 주기 전에 이미 생산성이 더 늘어 있었습니다(성과급은 성과를 뒤따라 지급됨).</li>
    </ul>
    <h2>미래 위험</h2>
    <p>다음 해 적자 확률과 영업이익률 범위는 노트북 6장 모델의 예측입니다. 최악·최적의 시나리오는 모델이 보는 하위·상위 10% 경우입니다. 적자 해를 가려내는 정확도가 높지 않아(AUC 0.66) 참고 지표로만 씁니다. 업계 불황 대비 점검은 그 업계가 과거에 실제로 겪은 충격(출처가 확인된 업황 사건 ${nEvents}건 포함)을 다시 적용하는 과거 재현입니다.</p>
    <h2>한계</h2>
    <ul>
      <li>1인당 급여는 급여총액÷직원수라 성과급·승진·직급 구성 차이를 다 지우지 못합니다.</li>
      <li>관찰 자료라 인과 효과를 증명하지 않습니다.</li>
      <li>노조 유무와 교섭력은 데이터에 없습니다.</li>
    </ul>
    <p class="muted small" style="margin-top:24px">Dart-B HR 학술제 MVP · 아이콘 Lucide(ISC) · 글꼴 Pretendard(OFL)</p>
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
