// JS 계산 엔진(js/engine.js)이 formula.py와 같은 숫자를 내는지 검사한다.
// 정답: tests/golden.json (scripts/make_golden.py가 data/*.json을 입력으로 formula.py를 돌려 만든 값)
// 실행: node tests/parity.test.mjs        (4_MVP 폴더에서)
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import * as E from '../js/engine.js';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const load = (p) => JSON.parse(readFileSync(join(ROOT, p), 'utf-8'));
const ctx = E.buildContext({
  firms: load('data/firms.json'), peers: load('data/peers.json'), forecast: load('data/forecast.json'),
  shocks: load('data/shocks.json'), catalog: load('data/catalog.json'), meta: load('data/meta.json'),
});
const gold = load('tests/golden.json');

const REL = 1e-9, ABS = 1e-6;
const fails = [];
let checked = 0;

function isMissing(v) {
  return v === null || v === undefined || (typeof v === 'number' && !Number.isFinite(v));
}

function same(g, j, path) {
  if (isMissing(g)) {
    checked += 1;
    if (!isMissing(j)) fails.push([path, g, j]);
    return;
  }
  if (Array.isArray(g)) {
    if (!Array.isArray(j) || j.length !== g.length) { fails.push([path, `배열 길이 ${g.length}`, j]); return; }
    g.forEach((x, i) => same(x, j[i], `${path}[${i}]`));
    return;
  }
  if (typeof g === 'object') {
    if (j === null || typeof j !== 'object') { fails.push([path, '객체', j]); return; }
    for (const k of Object.keys(g)) same(g[k], j[k], `${path}/${k}`);
    for (const k of Object.keys(j)) if (!(k in g)) fails.push([`${path}/${k}`, '(정답에 없음)', j[k]]);
    return;
  }
  checked += 1;
  if (typeof g === 'number') {
    if (typeof j !== 'number' || !(Math.abs(g - j) <= ABS + REL * Math.max(Math.abs(g), Math.abs(j)))) fails.push([path, g, j]);
    return;
  }
  if (g !== j) fails.push([path, g, j]);
}

for (const c of gold.cases) {
  const id = c.id;
  const p = `${c.name}(${id})`;
  c.pay_plan.forEach((t, i) => same(t.out, E.payPlan(ctx, id, t.args), `${p}/pay_plan[${i}]`));
  c.negotiation_range.forEach((t, i) => {
    const r = E.negotiationRange(ctx, id, t.args.peer_raise);
    same(t.out, r, `${p}/negotiation_range[${i}]`);
    for (const [rate, pos] of Object.entries(t.position)) same(pos, E.rangePosition(ctx, Number(rate), r), `${p}/range_position[${i}](${rate})`);
  });
  const co = c.compare_offers;
  same(co.out, E.compareOffers(ctx, id, co.args.union, co.args.company), `${p}/compare_offers`);
  c.profit_link_plan.forEach((t, i) => same(t.out, E.profitLinkPlan(ctx, id, t.args), `${p}/profit_link_plan[${i}]`));
  same(c.pay_plan_forecast.out, E.payPlanForecast(ctx, id, c.pay_plan_forecast.args), `${p}/pay_plan_forecast`);
  same(c.scenarios, E.scenarios(ctx, id), `${p}/scenarios`);
  c.stress_test.forEach((t, i) => same(t.out, E.stressTest(ctx, id, t.args), `${p}/stress_test[${i}]`));
}

console.log(`회사 ${gold.cases.length}곳 · 비교한 값 ${checked.toLocaleString()}개 · 불일치 ${fails.length}개`);
for (const f of fails.slice(0, 25)) console.log('  ', f[0], '| 정답:', JSON.stringify(f[1]), '| JS:', JSON.stringify(f[2]));
process.exit(fails.length ? 1 : 0);
