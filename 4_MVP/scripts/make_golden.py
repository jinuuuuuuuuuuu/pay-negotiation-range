"""2단계 JS 계산 엔진이 맞춰야 할 정답 숫자 세트(tests/golden.json)를 만든다.

- 앱과 똑같은 입력을 쓰도록 data/*.json을 다시 읽어 formula.py의 ctx를 만들고, formula 함수로 계산한다.
- 회사 표본: 상한 상태·지급 여력·기준 연도 충격·예측 대상 여부별로 고르고, 잘 알려진 회사를 더한다.
- 같은 계산을 반올림 전 원래 ctx로도 해서, 데이터 반올림(유효숫자 8자리)이 결과를 바꾸지 않는지 확인한다.
사용:  python make_golden.py   (export_data.py 다음에)
"""
import json
import math
import os
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_data as E  # noqa: E402

F = E.F
DATA = E.OUT
OUTP = os.path.join(E.MVP, 'tests', 'golden.json')
NAMED = ['현대자동차', '삼성전자', '기아', 'LG전자', 'SK하이닉스', 'HMM', '카카오', 'NAVER', '오뚜기', 'HD현대중공업',
         'LG유플러스', '셀트리온', '이마트', '한화오션']


def load(name):
    with open(os.path.join(DATA, name), encoding='utf-8') as f:
        return json.load(f)


def ctx_from_json():
    """앱이 받는 JSON → formula 함수가 쓰는 ctx/fc."""
    fj = load('firms.json')
    firms = pd.DataFrame(fj['rows'], columns=fj['cols']).set_index('id')
    inv = {v: k for k, v in E.FIRM_KEYS.items()}
    firms = firms.rename(columns=inv)
    firms['기준연도 업종 충격'] = firms['기준연도 업종 충격'].astype(bool)
    peers = load('peers.json')
    wT = firms['w_T']
    peer_w = {i: wT.reindex(p).to_numpy(dtype=float) for i, p in peers.items()}
    sj = load('shocks.json')
    t2 = pd.DataFrame([{'ind2': int(k.split('|')[0]), 'yr': int(k.split('|')[1]), **v} for k, v in sj['중분류'].items()]).set_index(['ind2', 'yr'])
    t1 = pd.DataFrame([{'sec': k.split('|')[0], 'yr': int(k.split('|')[1]), **v} for k, v in sj['대분류'].items()]).set_index(['sec', 'yr'])
    t0 = pd.DataFrame([{'yr': int(k), **v} for k, v in sj['전체'].items()]).set_index('yr')
    cat = pd.DataFrame(load('catalog.json'))
    cat['중분류코드'] = cat['중분류코드'].astype(str)
    meta = load('meta.json')
    ctx = SimpleNamespace(firms=firms, peer_w=peer_w, shocks={'중분류': t2, '대분류': t1, '전체': t0}, catalog=cat, end=meta['end'])
    fcj = load('forecast.json')
    fc = pd.DataFrame(fcj['rows'], columns=fcj['cols']).set_index('id')
    fc['범위예측_대상'] = fc['범위예측_대상'].astype(bool)
    return ctx, fc


def pick_firms(firms, fc, n_per=8, seed=7):
    rng = np.random.default_rng(seed)
    ids = set()
    for col in ['상한 상태', '지급 여력']:
        for _, g in firms.groupby(col):
            ids.update(rng.choice(g.index.to_numpy(), size=min(n_per, len(g)), replace=False))
    for mask in [firms['기준연도 업종 충격'], ~fc.reindex(firms.index)['범위예측_대상'].fillna(False).astype(bool)]:
        g = firms[mask]
        ids.update(rng.choice(g.index.to_numpy(), size=min(n_per, len(g)), replace=False))
    ids.update(firms.index[firms['name'].isin(NAMED)])
    return sorted(ids)


def ser(v):
    if isinstance(v, pd.DataFrame):
        out = {'rows': {str(k): {c: ser(x) for c, x in r.items()} for k, r in v.iterrows()},
               'order': [str(k) for k in v.index]}
        if v.attrs:
            out['attrs'] = {k: ser(x) for k, x in v.attrs.items()}
        return out
    if isinstance(v, pd.Series):
        return {str(k): ser(x) for k, x in v.items()}
    if isinstance(v, dict):
        return {str(k): ser(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [ser(x) for x in v]
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if (math.isnan(v) or math.isinf(v)) else float(v)
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


PAY = [dict(base_raise=0.03), dict(base_raise=0.05, bonus=0.01, headcount=0.05, sales_growth=0.04),
       dict(bonus=0.02), dict(base_raise=0.04, peer_raise=0.0)]
RATES = [0.0, 0.02, 0.035, 0.05, 0.08, 0.15]
LINK = [dict(), dict(alpha=0.10), dict(alpha=0.10, cap=0.10, floor=0.01)]
STRESS = [dict(), dict(base_raise=0.05, alpha=0.10, cap=0.10), dict(base_raise=0.03, severity='하위25'),
          dict(base_raise=0.03, with_sales=False), dict(base_raise=0.03, custom={'이익률': -0.03, '매출': -0.10})]


def cases(ctx, fc, ids):
    out = []
    for fid in ids:
        rec = {'id': fid, 'name': ctx.firms.loc[fid, 'name']}
        rec['pay_plan'] = [{'args': a, 'out': ser(F.pay_plan(ctx, fid, **a))} for a in PAY]
        rngs = []
        for pr in [None, 0.06]:
            r = F.negotiation_range(ctx, fid, peer_raise=pr)
            rngs.append({'args': {'peer_raise': pr}, 'out': ser(r),
                         'position': {str(x): F.range_position(x, r) for x in RATES}})
        rec['negotiation_range'] = rngs
        rec['compare_offers'] = {'args': {'union': {'base_raise': 0.07}, 'company': {'base_raise': 0.04, 'bonus': 0.01}},
                                 'out': ser(F.compare_offers(ctx, fid, union={'base_raise': 0.07},
                                                             company={'base_raise': 0.04, 'bonus': 0.01}))}
        rec['profit_link_plan'] = [{'args': a, 'out': ser(F.profit_link_plan(ctx, fid, **a))} for a in LINK]
        rec['pay_plan_forecast'] = {'args': {'base_raise': 0.03}, 'out': ser(F.pay_plan_forecast(ctx, fid, fc, base_raise=0.03))}
        rec['scenarios'] = ser(F.scenarios(ctx, fid))
        rec['stress_test'] = [{'args': a, 'out': ser(F.stress_test(ctx, fid, fc=fc, **a))} for a in STRESS]
        out.append(rec)
    return out


def max_rel_diff(a, b, path=''):
    """두 정답 세트의 숫자 최대 상대 차이와 문자열·논리값 불일치 목록."""
    worst, bad = 0.0, []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a:
            w, bb = max_rel_diff(a[k], b.get(k), f'{path}/{k}')
            worst, bad = max(worst, w), bad + bb
    elif isinstance(a, list) and isinstance(b, list):
        for i, (x, y) in enumerate(zip(a, b)):
            w, bb = max_rel_diff(x, y, f'{path}[{i}]')
            worst, bad = max(worst, w), bad + bb
    elif isinstance(a, float) and isinstance(b, (int, float)) and not isinstance(b, bool):
        worst = abs(a - b) / max(abs(a), abs(b), 1e-12) if abs(a - b) > 1e-9 else 0.0
    elif a != b:
        bad.append((path, a, b))
    return worst, bad


if __name__ == '__main__':
    ctx, fc = ctx_from_json()
    ids = pick_firms(ctx.firms, fc)
    gold = cases(ctx, fc, ids)
    os.makedirs(os.path.dirname(OUTP), exist_ok=True)
    meta = {'note': 'formula.py 함수를 앱과 같은 data/*.json 입력으로 실행한 정답. JS 엔진은 이 값과 상대오차 1e-9 이내로 같아야 함',
            'firms': len(ids), 'pay_args': PAY, 'rates': RATES, 'link_args': LINK, 'stress_args': STRESS}
    with open(OUTP, 'w', encoding='utf-8') as f:
        json.dump({'meta': meta, 'cases': gold}, f, ensure_ascii=False, allow_nan=False)
    print(f'정답 세트: {len(ids)}곳 → tests/golden.json ({os.path.getsize(OUTP) / 1024:,.0f} KB)')
    print('  상한 상태:', ctx.firms.loc[ids, '상한 상태'].value_counts().to_dict())
    # 반올림 영향: 원래 정밀도 ctx로 같은 계산
    core, B, ctx0, _ = E.build()
    ctx0.firms.index = ctx0.firms.index.astype(str)
    ctx0.peer_w = {str(k): v for k, v in ctx0.peer_w.items()}
    fc0 = F.load_forecast(os.path.join(E.RES, '4_모델링', '6_9_예측결과_2025.csv'))
    gold0 = cases(ctx0, fc0, ids)
    w, bad = max_rel_diff(gold, gold0)
    print(f'  반올림(유효숫자 {E.SIG}자리) 영향: 숫자 최대 상대 차이 {w:.2e}, 문자·판정 불일치 {len(bad)}건')
    for b in bad[:10]:
        print('   ', b)
