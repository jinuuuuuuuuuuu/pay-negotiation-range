"""MVP용 데이터 내보내기 — 진진진진 최종의 formula.py로 계산해 data/*.json을 만든다.

사용:  python export_data.py
- 계산은 2_코드/formula.py와 2_코드/run_산술식.py의 입력 읽기를 그대로 쓴다(결과 파일과 같은 숫자).
- 예측(6_9)과 사건카탈로그는 3_결과에서 읽는다.
- 업황 충격표는 CSV가 소수 둘째 자리로 반올림돼 있어, formula.shock_table로 반올림 전 값을 다시 계산한다.
- 끝에 3_결과의 CSV(MVP입력, 산술식결과, 업황충격표)와 같은지 검사한다.
- WPS 원자료는 내보내지 않는다(결과의 WPS 참고값은 10곳 이상 칸의 집계뿐).
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
MVP = os.path.dirname(HERE)
FINAL = os.path.dirname(MVP)                                   # 진진진진 최종
CODE = os.path.join(FINAL, '2_코드')
RES = os.path.join(FINAL, '3_결과')
OUT = os.path.join(MVP, 'data')
sys.path.insert(0, CODE)
import formula as F  # noqa: E402
import run_산술식 as R  # noqa: E402

START, END = 2023, 2025


SIG = 8                                                        # 소수 유효숫자 (크기 절약, 상대 오차 ~1e-8)


def clean(v):
    """JSON에 넣을 값: NaN/inf → None, numpy → 파이썬 기본형, 소수는 유효숫자 SIG자리."""
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        return None if (math.isnan(v) or math.isinf(v)) else float(f'{v:.{SIG}g}')
    if v is None or (isinstance(v, str) and v == ''):
        return v
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v


def columnar(recs):
    """[{k: v}] → {"cols": [...], "rows": [[...]]} (열 이름 반복 제거)."""
    cols = list(recs[0].keys()) if recs else []
    return {'cols': cols, 'rows': [[r.get(c) for c in cols] for r in recs]}


def dump(obj, name):
    p = os.path.join(OUT, name)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    print(f'  → data/{name} ({os.path.getsize(p) / 1024:,.0f} KB)')


def build():
    panel, core, wps = R.load_inputs()
    B = F.compute(core, START, END, wps=wps)
    catalog = F.load_catalog(os.path.join(RES, '3_산술식', '사건카탈로그.csv'))
    ctx = F.sim_context(B, core, catalog=catalog)
    return core, B, ctx, catalog


# 앱에서 쓰는 영문 키 (JS 코드 가독성). 계산 재료는 formula.sim_context와 같은 이름의 값
FIRM_KEYS = {
    'name': 'name', 'ind2': 'ind2', 'sec': 'sec', 'S_T': 'S_T', 'N_T': 'N_T', 'OP_T': 'OP_T', 'REV_T': 'REV_T',
    'D_T': 'D_T', 'opm_sd': 'opm_sd', 'opm': 'opm', 'sr': 'sr', 'sr_ref': 'sr_ref', 'w': 'w', 'w_T': 'w_T',
    '지급 여력': 'capacity', '비교군 인상률': 'peer_growth', 'α*': 'alpha_star', '이익÷급여': 'ops',
    '비교군 이익÷급여': 'peer_ops', 'S_avg': 'S_avg', 'OP_avg': 'OP_avg', 'REV_avg': 'REV_avg', 'N_avg': 'N_avg',
    '기준연도 업종 충격': 'base_shock', '하한': 'lower', '상한': 'upper', '상한 원값': 'upper_raw',
    '상한 표시': 'upper_show', '상한 상태': 'upper_state', '구간 해석': 'range_note',
}
# 진단 화면 표시용 (산술식결과 표의 열)
TABLE_KEYS = {
    '상장시장': 'market', '중분류': 'ind2_name', '대분류': 'sec_name', '직원수(구간 평균)': 'n_avg_window',
    '1인당 급여(만원)': 'wage_10k', '비교 20곳 중앙(만원)': 'peer_median_10k', '임금 차이(%)': 'wage_gap_pct',
    '비교군 안 순위(0~1)': 'rank', '임금 위치': 'wage_pos', '참고 임금 구간 하단(만원)': 'ref25_10k',
    '참고 임금 구간 상단(만원)': 'ref75_10k', '비교군 중 같은 중분류(곳)': 'peer_same_ind2', '비교군 구성': 'peer_mix',
    '비교군 주의': 'peer_warn', '영업이익률(%)': 'opm_pct', '업종 중앙 영업이익률(%)': 'opm_ind_pct',
    '업종 기준 단위': 'ind_unit', '여력 사유': 'capacity_reason', '현금흐름 표시': 'cf_flag',
    '인건비율 급여÷매출(%)': 'labor_ratio_pct', '비교 20곳 인건비율 중앙(%)': 'peer_labor_ratio_pct',
    '영업이익률 평소 변동(%p)': 'opm_sd_pctp', '인상5%_비용÷영업이익(%)': 'cost5_over_op_pct',
    '인상5%_영업이익률 하락(%p)': 'cost5_drop_pctp', 'WPS_성과배분제 운영률(%)': 'wps_ps_rate',
    'WPS_자발적 이직률 중앙(%)': 'wps_turnover', 'WPS_기준 표본': 'wps_n', 'WPS_단위': 'wps_unit',
    '급여 확인': 'pay_check', '진단문장': 'sentence',
}


def export(core, B, ctx, catalog):
    os.makedirs(OUT, exist_ok=True)
    f = ctx.firms.copy()
    t = F.to_table(B).set_index('기업고유코드')
    t.index = t.index.astype(str).str.zfill(8)
    code = core[core.yr == END].set_index('id')['종목코드'] if '종목코드' in core else pd.Series(dtype=str)
    firms = []
    for fid, r in f.iterrows():
        rec = {'id': str(fid)}
        rec.update({k: clean(r[c]) for c, k in FIRM_KEYS.items()})
        tr = t.loc[str(fid)] if str(fid) in t.index else None
        rec.update({k: (clean(tr[c]) if tr is not None and c in tr.index else None) for c, k in TABLE_KEYS.items()})
        sc = code.get(fid, None)
        rec['stock_code'] = None if sc is None or pd.isna(sc) else str(sc).split('.')[0].zfill(6)
        firms.append(rec)
    dump(columnar(firms), 'firms.json')

    peers = B.attrs['peers'].sort_values(['id', '순번'])
    dump({str(i): [str(p) for p in g.peer_id] for i, g in peers.groupby('id')}, 'peers.json')

    fc = F.load_forecast(os.path.join(RES, '4_모델링', '6_9_예측결과_2025.csv'))
    fc_cols = [c for c in fc.columns if c not in ('기업명',)]
    dump(columnar([{'id': str(i), **{c: clean(r[c]) for c in fc_cols}} for i, r in fc.iterrows()]), 'forecast.json')

    sh = ctx.shocks
    cols = ['기업수', '이익률변화', '이익률변화_하위25', '매출변화', '매출변화_하위25']
    shocks = {
        '중분류': {f'{i}|{y}': {**{c: clean(r[c]) for c in cols}, '큰충격': clean(r['큰충격'])} for (i, y), r in sh['중분류'].iterrows()},
        '대분류': {f'{s}|{y}': {c: clean(r[c]) for c in cols} for (s, y), r in sh['대분류'].iterrows()},
        '전체': {str(y): {c: clean(r[c]) for c in cols} for y, r in sh['전체'].iterrows()},
    }
    dump(shocks, 'shocks.json')

    cat_cols = ['사건ID', '사건명', '연도', '중분류코드', '중분류명', '확인수준', '기능4 선택지', '원인근거', '출처']
    dump([{c: clean(r[c]) for c in cat_cols if c in catalog.columns} for _, r in catalog.iterrows()], 'catalog.json')

    meta = {
        'start': START, 'end': END, 'firms': len(firms),
        'const': {'PAY_RATE': F.PAY_RATE, 'OVERHEAD_C': F.OVERHEAD_C, 'OVERHEAD_C_BASE': F.OVERHEAD_C_BASE,
                  'RANGE_UPPER_SHOW_MAX': F.RANGE_UPPER_SHOW_MAX, 'RANGE_HOLD_TEXT': F.RANGE_HOLD_TEXT,
                  'SHOCK_MIN_FIRMS': F.SHOCK_MIN_FIRMS, 'SHOCK_COMMON': F.SHOCK_COMMON,
                  'HIGH_P': F.HIGH_P, 'LOW_P': F.LOW_P, 'GSTAR_LIMIT': F.GSTAR_LIMIT},
        'ind2_name': {str(k): v for k, v in F.IND2_NAME.items()},
        'sec_name': F.SECTION_NAME,
        'source': 'DART 공시 패널 2015~2025 (진단 구간 2023~2025), 진진진진 최종/2_코드/formula.py로 계산. WPS 참고값은 10곳 이상 칸의 집계만.',
    }
    dump(meta, 'meta.json')
    return firms


def check(ctx, B):
    """3_결과의 CSV와 같은지 검사."""
    ok = True
    m = pd.read_csv(os.path.join(RES, '3_산술식', 'MVP입력_2023_2025.csv'), encoding='utf-8-sig', dtype={'id': str})
    m['id'] = m['id'].str.zfill(8)
    f = ctx.firms.copy()
    f.index = f.index.astype(str)
    m = m.set_index('id').loc[f.index]
    for c in f.columns:
        if c not in m.columns:
            continue
        a, b = f[c], m[c]
        if pd.api.types.is_numeric_dtype(a) and not pd.api.types.is_bool_dtype(a):
            same = np.allclose(a.astype(float), b.astype(float), rtol=1e-9, atol=1e-6, equal_nan=True)
        else:
            same = (a.fillna('').astype(str) == b.fillna('').astype(str)).all()
        if not same:
            ok = False
            print('  [불일치] MVP입력', c)
    for lvl in ['중분류', '대분류', '전체']:
        csv = pd.read_csv(os.path.join(RES, '3_산술식', f'업황충격표_{lvl}x연도.csv'), encoding='utf-8-sig')
        mine = ctx.shocks[lvl]
        val = (mine['이익률변화'] * 100).round(2).to_numpy()
        if not np.allclose(val, csv['영업이익률 변화 중앙(%p)'].to_numpy(), equal_nan=True):
            ok = False
            print('  [불일치] 업황충격표', lvl)
    t = F.to_table(B)
    csv = pd.read_csv(os.path.join(RES, '3_산술식', '산술식결과_2023_2025.csv'), encoding='utf-8-sig')
    for c in ['임금 위치', '지급 여력', '진단문장']:
        if not (t[c].astype(str).to_numpy() == csv[c].astype(str).to_numpy()).all():
            ok = False
            print('  [불일치] 산술식결과', c)
    print('  최종본 CSV와 대조:', '모두 같음' if ok else '불일치 있음')
    return ok


if __name__ == '__main__':
    core, B, ctx, catalog = build()
    export(core, B, ctx, catalog)
    sys.exit(0 if check(ctx, B) else 1)
