// 계산 엔진 — 진진진진 최종/2_코드/formula.py의 기능 2~4 함수를 그대로 옮긴 것.
// 출력 항목 이름은 formula.py와 같다(tests/golden.json과 바로 비교). 규칙을 바꿀 때는 formula.py를 먼저 고치고
// scripts/export_data.py → scripts/make_golden.py → node tests/parity.test.mjs 순서로 다시 맞춘다.
// 업황 충격은 기능 4(업계 불황 대비 점검)에서만 쓴다. 진단·인상안 협상 구간·이익연동 전환은 평상시 기준.

const isNum = (v) => typeof v === 'number' && !Number.isNaN(v);
const nn = (v) => (v === null || v === undefined ? NaN : v);          // JSON null → NaN (null*2 = 0 방지)

// ---------------------------------------------------------------- 데이터 → ctx
function table(t) {
  // {"cols":[...], "rows":[[...]]} → 행 객체 배열. 숫자 열의 null은 NaN으로
  const numCols = new Set();
  t.cols.forEach((c, j) => {
    for (const r of t.rows) {
      const v = r[j];
      if (v === null || v === undefined) continue;
      if (typeof v === 'number') numCols.add(c);
      break;
    }
  });
  return t.rows.map((r) => {
    const o = {};
    t.cols.forEach((c, j) => { o[c] = numCols.has(c) ? nn(r[j]) : r[j]; });
    return o;
  });
}

export function buildContext({ firms, peers, forecast, shocks, catalog, meta }) {
  const fm = new Map();
  for (const f of table(firms)) fm.set(f.id, f);
  const peerW = new Map();
  for (const [id, list] of Object.entries(peers)) {
    peerW.set(id, list.map((p) => (fm.has(p) ? fm.get(p).w_T : NaN)));
  }
  const fc = new Map();
  for (const r of table(forecast)) fc.set(r.id, r);
  const toMap = (obj) => {
    const m = new Map();
    for (const [k, v] of Object.entries(obj)) {
      const o = {};
      for (const [kk, vv] of Object.entries(v)) o[kk] = typeof vv === 'boolean' || typeof vv === 'string' ? vv : nn(vv);
      m.set(k, o);
    }
    return m;
  };
  return {
    firms: fm, peerW, fc,
    shocks: { 중분류: toMap(shocks['중분류']), 대분류: toMap(shocks['대분류']), 전체: toMap(shocks['전체']) },
    catalog, end: meta.end, C: meta.const, meta,
  };
}

// ---------------------------------------------------------------- 공통
function nanMedian(arr) {
  const a = arr.filter(isNum).sort((x, y) => x - y);
  if (!a.length) return NaN;
  const m = a.length >> 1;
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

function rank(w, arr) {
  // formula._rank: 비교군 안 순위 (같으면 0.5). w가 NaN이면 비교가 모두 거짓이라 0
  const a = arr.filter(isNum);
  if (!a.length) return NaN;
  let lt = 0, eq = 0;
  for (const x of a) { if (x < w) lt += 1; else if (x === w) eq += 1; }
  return (lt + 0.5 * eq) / a.length;
}

const div = (a, b) => a / b;                                            // 0으로 나누면 Infinity/NaN (파이썬 numpy와 같음)

function pctFmt(x, digits) {
  // 파이썬 f'{x:.1%}'와 같게: x×100을 소수 digits자리로 (반올림은 가장 가까운 값, 정확히 반이면 짝수)
  const s = (x * 100).toFixed(digits + 3);
  const v = Number(s);
  const p = 10 ** digits;
  let r = Math.round(v * p);
  if (Math.abs(v * p - Math.trunc(v * p)) === 0.5 && r % 2 !== 0) r -= 1;
  return `${(r / p).toFixed(digits)}%`;
}

// ---------------------------------------------------------------- 기능 2: 인상 결정
export function payPlan(ctx, id, { base_raise = 0, bonus = 0, headcount = 0, sales_growth = 0, peer_raise = null } = {}) {
  const f = ctx.firms.get(id);
  const c = ctx.C.OVERHEAD_C, cBase = ctx.C.OVERHEAD_C_BASE;
  const S0 = f.S_T, N0 = f.N_T, REV = f.REV_T, OP = f.OP_T;
  const S1 = S0 * (1 + headcount) * (1 + base_raise);
  const B1 = bonus * S1;
  const dHead = S0 * headcount * (1 + cBase);
  const dRaise = S0 * (1 + headcount) * base_raise * (1 + cBase);
  const dBonus = B1 * (1 + c);
  const dW = dHead + dRaise + dBonus;
  const REV1 = REV * (1 + sales_growth);
  const OPpre = OP + (REV1 - REV) * (REV > 0 ? OP / REV : 0);
  const N1 = N0 * (1 + headcount);
  const A = S0 + OP + (isNum(f.D_T) ? f.D_T : 0);
  const drop = REV1 > 0 ? (dW / REV1) * 100 : NaN;
  const gPeer = peer_raise === null || peer_raise === undefined ? f.peer_growth : peer_raise;
  const pw = ctx.peerW.get(id) || [];
  const wNow = f.w_T, wNext = f.w_T * (1 + base_raise) * (1 + bonus);
  const pwNext = pw.map((x) => x * (1 + (isNum(gPeer) ? gPeer : 0)));
  const medNow = pw.length ? nanMedian(pw) : NaN;
  const medNext = pw.length ? nanMedian(pwNext) : NaN;
  return {
    '기본급 인상률': base_raise, '일시 성과급(급여 대비)': bonus, '인원 증감': headcount, '매출 증가율': sales_growth,
    '회사 부담 증가(1년)': dW, '그중 인원분': dHead, '그중 기본급 인상분': dRaise, '그중 성과급분': dBonus,
    '3년 누적 부담(인원·기본급 유지 + 성과급 1회)': 3 * (dHead + dRaise) + dBonus,
    '지급 전 영업이익(내년)': OPpre, '지급 후 영업이익(내년)': OPpre - dW,
    '영업이익률 하락(%p)': drop,
    '비용÷영업이익(%)': OPpre > 0 ? (dW / OPpre) * 100 : NaN,
    '지급 때문에 적자 전환': OPpre >= 0 && OPpre - dW < 0,
    'g*(%)': A > 0 ? (dW / A) * 100 : NaN,
    '평소 변동 대비': isNum(f.opm_sd) && f.opm_sd > 0 ? drop / (f.opm_sd * 100) : NaN,
    '올해 급여총액': S0, '내년 급여총액(성과급 포함)': S1 + B1, '내년 직원수': N1, '내년 1인당 급여': div(S1 + B1, N1),
    '내년 매출': REV1, '내년 영업이익률(%)': REV1 > 0 ? ((OPpre - dW) / REV1) * 100 : NaN,
    '내년 인건비율(%)': REV1 > 0 ? ((S1 + B1) / REV1) * 100 : NaN,
    '비교 20곳 인건비율 중앙(%)': f.sr_ref * 100,
    '비교군 인상률 가정': gPeer,
    '지금 순위(마지막 해)': rank(wNow, pw), '내년 예상 순위': rank(wNext, pwNext),
    '지금 임금 차이(%)': (wNow / medNow - 1) * 100, '내년 예상 임금 차이(%)': (wNext / medNext - 1) * 100,
  };
}

// ---------------------------------------------------------------- 기능 2: 협상 구간 (결정표 14장)
function rangeCore(ctx, lower, ops, peerOps, opT, sT) {
  const C = ctx.C;
  const out = { 하한: lower, 상한: NaN, '상한 원값': NaN, '상한 표시': '', '상한 상태': '', '구간 해석': '' };
  if (!isNum(lower)) {
    out['상한 상태'] = '비교군 인상률 없음';
    out['상한 표시'] = '비교군 인상률 없음';
    return out;
  }
  if (!isNum(peerOps) || peerOps <= 0) {
    out['상한 상태'] = C.RANGE_HOLD_TEXT;
    out['상한 표시'] = C.RANGE_HOLD_TEXT;
    out['구간 해석'] = '하한(업계 인상률)만 제시. 고정 인상보다 이익연동 전환을 함께 검토';
    return out;
  }
  let raw, state;
  if (!isNum(ops) || ops <= 0) { raw = 0; state = '3년 합산 영업적자'; }
  else { raw = (lower * ops) / peerOps; state = '계산'; }
  const cap = isNum(opT) && opT > 0 && sT > 0 ? opT / (sT * (1 + C.OVERHEAD_C_BASE)) : 0;
  const upper = Math.min(raw, cap);
  if (state === '계산' && cap < raw) state = '적자 전환 직전에서 제한';
  out['상한'] = upper;
  out['상한 원값'] = raw;
  out['상한 상태'] = state;
  out['상한 표시'] = upper > C.RANGE_UPPER_SHOW_MAX ? `${Math.round(C.RANGE_UPPER_SHOW_MAX * 100)}% 초과` : pctFmt(upper, 1);
  out['구간 해석'] = upper >= lower ? '업계 수준 이상도 업계만큼의 부담으로 감당 가능' : '업계만큼 주면 우리 부담이 업계보다 큼. 이익연동 전환 검토';
  return out;
}

export function negotiationRange(ctx, id, peerRaise = null) {
  const f = ctx.firms.get(id);
  const lower = peerRaise === null || peerRaise === undefined ? f.peer_growth : peerRaise;
  const ops = f.S_avg > 0 ? f.OP_avg / f.S_avg : NaN;
  return rangeCore(ctx, lower, ops, f.peer_ops, f.OP_T, f.S_T);
}

export function rangePosition(ctx, rate, rng) {
  const lo = rng['하한'], up = rng['상한'], max = ctx.C.RANGE_UPPER_SHOW_MAX;
  if (!isNum(lo)) return '';
  if (!isNum(up)) return rate < lo ? '하한 미달' : '하한 이상 (상한 산출 보류)';
  if (up >= lo) {
    if (rate < lo) return '하한 미달';
    if (up > max) return `구간 안 (상한 ${Math.round(max * 100)}% 초과)`;
    return rate <= up ? '구간 안' : '상한 초과';
  }
  if (rate <= up) return '상한 이하';
  return rate < lo ? '상한 초과·하한 미달' : '하한 이상·상한 초과';
}

export function compareOffers(ctx, id, union, company, plan = {}) {
  const a = payPlan(ctx, id, { ...union, ...plan });
  const b = payPlan(ctx, id, { ...company, ...plan });
  const rng = negotiationRange(ctx, id, plan.peer_raise ?? null);
  for (const x of [a, b]) {
    x['협상 구간 하한'] = rng['하한'];
    x['협상 구간 상한'] = rng['상한 표시'];
    x['구간 위치'] = rangePosition(ctx, x['기본급 인상률'], rng);
  }
  const rows = {};
  for (const k of Object.keys(a)) {
    const u = a[k], v = b[k];
    const num = typeof u === 'number';
    rows[k] = { 노조안: u, 회사안: v, '차이(노조안 − 회사안)': num ? u - v : NaN };
  }
  return { rows, order: Object.keys(a) };
}

// ---------------------------------------------------------------- 기능 3: 이익연동 전환
function linkPay(alpha, op, s, cap, floor) {
  let pay = isNum(op) && isNum(alpha) ? alpha * Math.max(op, 0) : NaN;
  if (isNum(pay) && floor !== null && floor !== undefined) pay = Math.max(pay, floor * s);
  if (isNum(pay) && cap !== null && cap !== undefined) pay = Math.min(pay, cap * s);
  return pay;
}

export function profitLinkPlan(ctx, id, { alpha = null, cap = null, floor = null } = {}) {
  const f = ctx.firms.get(id);
  const rate = ctx.C.PAY_RATE, c = ctx.C.OVERHEAD_C;
  const a = alpha === null ? f.alpha_star : alpha;
  const S = f.S_avg, N = f.N_avg, OP = f.OP_avg;
  const fixed = rate * S;
  const pay = linkPay(a, OP, S, cap, floor);
  return {
    '적용 비율(영업이익 대비)': a, '상한(급여 대비)': cap, '하한(급여 대비)': floor,
    '영업이익(3년 연평균)': OP,
    '고정 지급(급여 대비 rate)': fixed, '연동 지급': pay, '연동 ÷ 고정': fixed > 0 ? pay / fixed : NaN,
    '급여 대비 지급률(%)': S > 0 ? (pay / S) * 100 : NaN,
    '1인당 연동 지급': N > 0 ? pay / N : NaN, '1인당 고정 지급': N > 0 ? fixed / N : NaN,
    '회사 부담(연동)': isNum(pay) ? pay * (1 + c) : NaN,
    '연동 부담 ÷ 영업이익(%)': isNum(pay) && OP > 0 ? ((pay * (1 + c)) / OP) * 100 : NaN,
    '고정 부담 ÷ 영업이익(%)': OP > 0 ? ((fixed * (1 + c)) / OP) * 100 : NaN,
    '0원 지급': isNum(OP) && OP <= 0 && (floor === null || floor === undefined),
  };
}

// ---------------------------------------------------------------- 기능 4: 미래 위험
const FORECAST_CASES = [['P10', '나쁜 쪽(P10)'], ['P50', '중앙(P50)'], ['P90', '좋은 쪽(P90)']];

export function payPlanForecast(ctx, id, { base_raise = 0, bonus = 0, headcount = 0, sales_growth = null, peer_raise = null } = {}) {
  const r = ctx.fc.get(id);
  if (!r || !r['범위예측_대상']) {
    return {
      rows: {}, order: [],
      attrs: { 안내: '범위 예측 대상이 아님 (여력 제약이거나 마지막 해 매출 없음). 다음 해 적자 확률만 참고', '다음 해 적자 확률': r ? r['다음해_적자확률'] : NaN },
    };
  }
  const g = sales_growth === null ? Math.expm1(r['매출 성장_P50']) : sales_growth;
  const plan = payPlan(ctx, id, { base_raise, bonus, headcount, sales_growth: g, peer_raise });
  const dW = plan['회사 부담 증가(1년)'], REV1 = plan['내년 매출'];
  const rows = {}, order = [];
  for (const [q, label] of FORECAST_CASES) {
    const m = r[`영업이익률_${q}`];
    const pre = REV1 * m, post = pre - dW;
    rows[label] = {
      '예측 영업이익률(%)': m * 100, '내년 매출': REV1, '지급 전 영업이익': pre, '회사 부담 증가': dW, '지급 후 영업이익': post,
      '지급 후 영업이익률(%)': REV1 > 0 ? (post / REV1) * 100 : NaN,
      '비용÷영업이익(%)': pre > 0 ? (dW / pre) * 100 : NaN,
      '지급 후 적자': post < 0, '지급 때문에 적자 전환': pre >= 0 && post < 0,
    };
    order.push(label);
  }
  return {
    rows, order,
    attrs: { '다음 해 적자 확률': r['다음해_적자확률'], '적용 매출 증가율': g,
      '매출 증가율 범위(P10~P90)': [Math.expm1(r['매출 성장_P10']), Math.expm1(r['매출 성장_P90'])] },
  };
}

export function firmShock(ctx, ind2, sec, yr, severity = '중앙') {
  const sfx = severity === '하위25' ? '_하위25' : '';
  const min = ctx.C.SHOCK_MIN_FIRMS;
  const tries = [['중분류', ctx.shocks['중분류'], `${ind2}|${yr}`], ['대분류', ctx.shocks['대분류'], `${sec}|${yr}`], ['전체', ctx.shocks['전체'], `${yr}`]];
  for (const [unit, t, key] of tries) {
    const r = t.get(key);
    if (r && (unit === '전체' || r['기업수'] >= min)) {
      return { 이익률변화: r[`이익률변화${sfx}`], 매출변화: r[`매출변화${sfx}`], 단위: unit, 기업수: Math.trunc(r['기업수']) };
    }
  }
  return { 이익률변화: NaN, 매출변화: NaN, 단위: '', 기업수: 0 };
}

export function scenarios(ctx, id) {
  const f = ctx.firms.get(id);
  const end = ctx.end, ind2 = Math.trunc(f.ind2);
  const out = [];
  for (const [k, y] of Object.entries(ctx.C.SHOCK_COMMON)) {
    if (y < end) out.push({ 경우: `${k} (${y})`, 종류: '공통 사건', 연도: y, 근거: '공통 시나리오' });
  }
  const cat = ctx.catalog || [];
  for (const r of cat) {
    if (r['기능4 선택지'] === '공통 시나리오 후보' && r['연도'] < end) {
      out.push({ 경우: `${r['사건명']} (${r['연도']})`, 종류: '공통 사건', 연도: Math.trunc(r['연도']), 근거: `${r['확인수준']} (공통 시나리오 후보)` });
    }
  }
  for (const r of cat) {
    if (String(r['중분류코드']) === String(ind2) && String(r['기능4 선택지'] || '').startsWith('이름 붙여') && r['연도'] < end) {
      const tag = r['확인수준'] === '부분확인' ? ' (일부 근거)' : '';
      out.push({ 경우: `${r['사건명']} (${r['연도']})${tag}`, 종류: '우리 업종 사건', 연도: Math.trunc(r['연도']), 근거: r['확인수준'] });
    }
  }
  // 우리 업종 최악의 해: 같은 중분류(최소 기업 수 이상), 기준 연도 이전 중 영업이익률 변화가 가장 작은 해 (처음 나온 값)
  let best = null;
  for (const [key, r] of ctx.shocks['중분류']) {
    const [i, y] = key.split('|').map(Number);
    if (i !== ind2 || !(r['기업수'] >= ctx.C.SHOCK_MIN_FIRMS) || !(y < end) || !isNum(r['이익률변화'])) continue;
    if (best === null || r['이익률변화'] < best.v) best = { y, v: r['이익률변화'] };
  }
  if (best) {
    const named = out.filter((o) => o['종류'] === '우리 업종 사건' && o['연도'] === best.y);
    if (named.length) named[0]['경우'] += ' · 우리 업종 최악의 해';
    else out.push({ 경우: `우리 업종 최악의 해 (${best.y})`, 종류: '최악의 해', 연도: best.y, 근거: '데이터' });
  }
  return out;
}

export function stressTest(ctx, id, { base_raise = 0, bonus = 0, headcount = 0, sales_growth = 0, alpha = null, cap = null,
  floor = null, severity = '중앙', with_sales = true, custom = null, useForecast = true } = {}) {
  const f = ctx.firms.get(id);
  const plan = payPlan(ctx, id, { base_raise, bonus, headcount, sales_growth });
  const link = profitLinkPlan(ctx, id, { alpha, cap, floor });
  const dW = plan['회사 부담 증가(1년)'], REV1 = plan['내년 매출'];
  const mT = f.REV_T > 0 ? f.OP_T / f.REV_T : NaN;
  const mAvg = f.REV_avg > 0 ? f.OP_avg / f.REV_avg : NaN;
  const a = link['적용 비율(영업이익 대비)'];
  const fixed = link['고정 지급(급여 대비 rate)'];
  const rows = {}, order = [];

  function row(name, kind, yr, basis, rev1, opPre, opAvg, dm = NaN, dr = NaN, unit = '') {
    const post = opPre - dW;
    const pay = linkPay(a, opAvg, f.S_avg, cap, floor);
    rows[name] = {
      종류: kind, 연도: yr, 근거: basis, '충격 단위': unit,
      '영업이익률 변화(%p)': isNum(dm) ? dm * 100 : NaN, '매출 변화(%)': isNum(dr) ? dr * 100 : NaN,
      '내년 매출': rev1, '지급 전 영업이익': opPre, '인상안 회사 부담': dW, '지급 후 영업이익': post,
      '지급 후 영업이익률(%)': rev1 > 0 ? (post / rev1) * 100 : NaN,
      '비용÷영업이익(%)': opPre > 0 ? (dW / opPre) * 100 : NaN,
      '지급 때문에 적자 전환': opPre >= 0 && post < 0, '지급 후 적자': post < 0,
      '이익연동 지급': pay, '이익연동 ÷ 고정': fixed > 0 ? pay / fixed : NaN,
    };
    order.push(name);
  }

  row('평상시', '평상시', ctx.end, '기능 2·3의 결과', REV1, plan['지급 전 영업이익(내년)'], f.OP_avg);
  const r = ctx.fc.get(id);
  if (useForecast && r && r['범위예측_대상']) {
    const revM = f.REV_T * (1 + headcount * 0) * Math.exp(r['매출 성장_P50']);
    for (const [q, label] of [['P50', '모델 중앙(P50)'], ['P10', '모델 나쁜 쪽(P10)']]) {
      const m = r[`영업이익률_${q}`];
      row(label, '모델 예측', ctx.end + 1, '노트북 6장 모델 D', revM, revM * m, f.REV_avg * m);
    }
  }
  function apply(name, kind, yr, basis, dm, dr, unit) {
    const d = with_sales ? dr : 0;
    if (!isNum(dm)) return;
    const rev1 = REV1 * (1 + d);
    const opAvg = f.REV_avg * (1 + d) * (mAvg + dm);
    row(name, kind, yr, basis, rev1, rev1 * (mT + dm), opAvg, dm, d, unit);
  }
  for (const sc of scenarios(ctx, id)) {
    const sh = firmShock(ctx, Math.trunc(f.ind2), f.sec, sc['연도'], severity);
    apply(sc['경우'], sc['종류'], sc['연도'], sc['근거'], sh['이익률변화'], sh['매출변화'], `${sh['단위']} ${sh['기업수']}곳`);
  }
  if (custom) apply('직접 입력', '직접 입력', null, '사용자 입력', custom['이익률'] ?? 0, custom['매출'] ?? 0, '');
  const attrs = {
    강도: severity !== '하위25' ? '업종의 보통 회사(중앙)' : '업종에서 많이 맞은 회사(하위 25%)',
    '매출 충격': with_sales,
  };
  if (f.base_shock) attrs['기준 연도 경고'] = `${ctx.end}년이 이미 이 업종의 큰 충격 해라, 그 위에 충격을 더 얹은 결과입니다`;
  if (useForecast && r) attrs['다음 해 적자 확률'] = r['다음해_적자확률'];
  return { rows, order, attrs };
}
