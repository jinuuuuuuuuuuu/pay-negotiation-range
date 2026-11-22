"""추가 가설검정 H7(임금 → 자발적 이직률), H8(성과배분 → 생산성) — 사전 계획: 결정표 13장, 가설검정_추가_사전계획.md

WPS 원자료는 이용 조건상 공유하지 않는다. 이 모듈은 집계 결과(회귀 계수표)만 만든다.
사용:  import wps_hypothesis as WH ; tables = WH.main(wps_path, out=None, quiet=True)   (노트북 4장 H7·H8)
       python wps_hypothesis.py [WPS_통합.csv 경로] [결과 폴더]
"""
import glob
import os
import sys
import unicodedata

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import formula as F  # noqa: E402

DATA = os.environ.get('HR_DATA_DIR', os.path.join(os.path.expanduser('~'), 'Downloads'))
OUT = None          # main(out=...)으로 지정하면 CSV도 저장
QUIET = False
RESULTS = {}

# ---------------------------------------------------------------- 사전 고정값
BOUND_H7 = 0.5      # %p, 임금 10%당 자발적 이직률
BOUND_H8 = 1.4      # %, 성과배분 실시 → 2년 뒤 1인당 부가가치 변화
ALPHA = 0.05
MINWAGE_HOURLY = {2015: 5580, 2017: 6470, 2019: 8350, 2021: 8720, 2023: 9620}   # 원, 월 209시간
SIZE_BINS = [0, 29, 99, 299, 999, np.inf]
SIZE_LABELS = ['10~29', '30~99', '100~299', '300~999', '1000~']
LN10 = np.log(1.1)


# ---------------------------------------------------------------- 1. WPS 변수 만들기
def find_wps(path=None):
    """파일 이름이 자모 분리형(NFD)일 수 있어 NFC로 맞춰 찾는다."""
    if path and os.path.exists(path):
        return path
    folder = os.path.dirname(path) if path else DATA
    want = unicodedata.normalize('NFC', os.path.basename(path)) if path else 'WPS_통합.csv'
    hits = [p for p in glob.glob(os.path.join(folder, '*.csv'))
            if unicodedata.normalize('NFC', os.path.basename(p)) == want]
    if not hits:
        raise FileNotFoundError(want)
    return hits[0]


COLS = ['id', 'year', 'ind10', 'ind9', 'aq1001', 'aq2001', 'aq2003', 'fpq1001', 'fpq1011', 'epq3008', 'epq3028', 'epq3038', 'epq4008',
        'epq8031', 'epq8041', 'epq7001', 'cq3001', 'cq3002', 'cq3007', 'cpi',
        'fpq2001', 'fpq2006', 'fpq2007', 'fpq2008', 'fpq2009', 'fpq2010', 'fpq2011', 'fpq2015',
        'fpq3001', 'fpq3002', 'fpq3003', 'fpq3005', 'fpq3006', 'fpq3007']


def build_wps(path=None):
    w = pd.read_csv(find_wps(path), usecols=COLS, low_memory=False).apply(pd.to_numeric, errors='coerce')
    log = [('WPS 2015~2023 전체', len(w), w.id.nunique())]
    w['ind2'] = w.ind10.fillna(w.ind9)
    w = w[w.ind2.notna()].copy()
    w['ind2'] = w.ind2.astype(int)
    w['sec'] = w.ind2.map(F.ksic_section)
    w = w[w.aq2001.eq(2) & ~w.sec.isin(['K', 'O'])].copy()
    log.append(('민간 회사법인, 금융·공공 제외', len(w), w.id.nunique()))
    w = w[w.epq4008.ge(10)].copy()
    log.append(('연말 정규직 10명 이상', len(w), w.id.nunique()))

    defl = 111.590 / w.cpi                                            # 2023년 가격
    n = w.fpq1011.where(w.fpq1011.ge(10))
    # 이직
    w['turn'] = (w.epq8041 / w.epq4008 * 100).where(lambda s: s.le(150))
    w['turn_all'] = (w.epq8031 / w.epq4008 * 100).where(lambda s: s.le(150))
    # 임금
    pay = (w.fpq2006 + w.fpq3001.fillna(0)).where(w.fpq2006.notna())
    wage_nom = pay / n                                                # 백만 원
    floor = w.year.map(MINWAGE_HOURLY) * 209 * 12 / 1e6 * 0.8
    wage_nom = wage_nom.where(wage_nom.ge(floor) & wage_nom.le(300))
    w['lw'] = np.log(wage_nom * defl)
    w['wage_real'] = wage_nom * defl
    w['cost_ok'] = w.fpq3001.notna() | ~w.sec.eq('C')                  # 제조업인데 원가 급여가 비지 않은 행
    # 규모, 임금 위치
    w['lsize'] = np.log(n)
    w['size'] = pd.cut(n, SIZE_BINS, labels=SIZE_LABELS).astype(str)
    g = w.groupby(['sec', 'size', 'year']).lw
    med = g.transform('median').where(g.transform('count').ge(5), w.groupby(['sec', 'year']).lw.transform('median'))
    w['wpos'] = (w.lw - med) * 100                                   # 동종 중앙 대비 (로그 %)
    # 성과배분
    w['bonus'] = np.select([w.cq3001.eq(2), w.cq3002.eq(1), w.cq3002.eq(2)], [0.0, 1.0, 0.0], np.nan)
    lv = (w.cq3007 / 100).where(w.cq3007.lt(9_000_000) & w.cq3007.le(1200))
    w['bonus_m'] = np.where(w.bonus.eq(0), 0.0, np.where(w.bonus.eq(1), lv, np.nan))
    # 부가가치·매출·이익률
    va_cost = ['fpq2006', 'fpq2007', 'fpq2008', 'fpq2009', 'fpq2010', 'fpq2011',
               'fpq3001', 'fpq3002', 'fpq3003', 'fpq3005', 'fpq3006', 'fpq3007']
    va = (w.fpq2015 + w[va_cost].fillna(0).sum(axis=1)).where(w.fpq2015.notna() & w.fpq2006.notna())
    va_pw = va / n * defl
    w['lva'] = np.log(va_pw.where(va_pw.gt(0)))
    lab = w[['fpq2006', 'fpq2007', 'fpq2008', 'fpq3001', 'fpq3002', 'fpq3003']].fillna(0).sum(axis=1)
    w['va_pw'] = va_pw.where(va_pw.gt(0))
    w['lab_pw'] = (lab / n * defl).where(w['va_pw'].notna())
    rev = w.fpq2001.where(w.fpq2001.gt(0) & w.fpq2001.lt(9_000_000))
    w['lrev'] = np.log(rev / n * defl)
    w['opm'] = (w.fpq2015 / rev * 100).where(lambda s: s.abs().le(100))
    # 통제
    w['reg_share'] = (w.epq4008 / w.epq3008).where(w.epq3008.gt(0)).clip(upper=1)
    w['union'] = w.epq7001.gt(0).astype(float)
    w['sen_share'] = (w.epq3038 / w.epq3008).where(w.epq3008.gt(0)).clip(upper=1)   # 근속 20년 이상 비중
    w['fem_share'] = (w.epq3028 / w.epq3008).where(w.epq3008.gt(0)).clip(upper=1)
    w['single'] = w.aq1001.eq(1) | w.fpq1001.eq(1)
    w['indyr'] = w.ind2.astype(str) + '_' + w.year.astype(str)
    # 다음 회차(t+2)
    w = w.sort_values(['id', 'year'])
    nxt = w.groupby('id').shift(-1)
    ok = nxt.year.eq(w.year + 2)
    for c in ['turn', 'lva', 'lrev', 'opm', 'bonus', 'va_pw', 'lab_pw']:
        w[c + '_f'] = nxt[c].where(ok)
    prv = w.groupby('id').shift(1)
    okp = prv.year.eq(w.year - 2)
    w['lva_p'] = prv['lva'].where(okp)
    w['bonus_p'] = prv['bonus'].where(okp)
    w['dlva_pre'] = (w.lva - w.lva_p) * 100                          # 사전 추세 (t−2 → t)
    # 부가가치 변화(t → t+2)를 인건비 부분과 나머지(영업이익·감가 등)로 나눔, 기준 = t년 1인당 부가가치
    w['dva_lab'] = (w.lab_pw_f - w.lab_pw) / w.va_pw * 100
    w['dva_nonlab'] = ((w.va_pw_f - w.va_pw) - (w.lab_pw_f - w.lab_pw)) / w.va_pw * 100
    w['dlva'] = (w.lva_f - w.lva) * 100
    w['dlrev'] = (w.lrev_f - w.lrev) * 100
    w['dopm'] = w.opm_f - w.opm
    return w.reset_index(drop=True), log


# ---------------------------------------------------------------- 2. 회귀 도구
def absorb(frame, cols, fes, tol=1e-9, it=500):
    out = frame[cols].astype(float).copy()
    for _ in range(it):
        prev = out.copy()
        for fe in fes:
            out = out - out.groupby(frame[fe]).transform('mean')
        if (out - prev).abs().to_numpy().max() < tol:
            break
    return out


def winsor(s, lo=.01, hi=.99):
    a, b = s.quantile([lo, hi])
    return s.clip(a, b)


def fe_reg(d, y, xs, fes, cluster='id', scale=None, bound=None, label='', wins=False):
    """고정효과 흡수 OLS + 사업체 클러스터 표준오차. 첫 번째 x의 효과를 scale배로 보고."""
    d = d.dropna(subset=[y] + xs + fes).copy()
    if fes and 'id' in fes:                                          # 기업 FE는 2회 이상 관측된 곳만
        d = d[d.groupby('id')[y].transform('count').ge(2)]
    if wins:
        for c in [y] + xs:
            if d[c].nunique() > 2:
                d[c] = winsor(d[c])
    dm = absorb(d, [y] + xs, fes) if fes else d[[y] + xs] - d[[y] + xs].mean()
    fit = sm.OLS(dm[y], dm[xs]).fit(cov_type='cluster', cov_kwds={'groups': d[cluster]})
    x0 = xs[0]
    k = scale or 1.0
    b, se = fit.params[x0] * k, fit.bse[x0] * k
    ncl = d[cluster].nunique()
    lo95, hi95 = b - 1.96 * se, b + 1.96 * se
    row = {'모형': label, '관측': len(d), '사업체': ncl, '효과': b, 'SE': se, '95% 하한': lo95, '95% 상한': hi95,
           'p(효과=0)': float(fit.pvalues[x0])}
    if bound is not None:
        t = stats.t
        row['90% 하한'] = b - t.ppf(.95, ncl - 1) * se
        row['90% 상한'] = b + t.ppf(.95, ncl - 1) * se
        row['TOST p'] = max(t.sf((b + bound) / se, ncl - 1), t.cdf((b - bound) / se, ncl - 1))
    return row


CTRL = ['lsize', 'reg_share', 'union']


def table(rows, name):
    t = pd.DataFrame(rows)
    num = t.select_dtypes('number').columns
    t[num] = t[num].round(4)
    RESULTS[name] = t
    if OUT:
        t.to_csv(os.path.join(OUT, name), index=False, encoding='utf-8-sig')
    if not QUIET:
        print(f'\n[{name}]')
        print(t.to_string(index=False))
    return t


def holm(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    adj = np.empty_like(p)
    run = 0
    for r, i in enumerate(o):
        run = max(run, (len(p) - r) * p[i])
        adj[i] = min(run, 1)
    return adj


# ---------------------------------------------------------------- 3. 분석
def main(wps_path=None, out=None, quiet=False, dart=True):
    """H7·H8 전부 실행. 표는 반환값(dict)과 out 폴더 CSV에 담긴다."""
    global OUT, QUIET
    OUT, QUIET = out, quiet
    RESULTS.clear()
    if OUT:
        os.makedirs(OUT, exist_ok=True)
    pd.set_option('display.width', 250)
    w, log = build_wps(wps_path)
    table([{'단계': a, '행': b, '사업체': c} for a, b, c in log], '0_표본흐름.csv')
    desc = w[['turn', 'turn_all', 'wage_real', 'wpos', 'bonus', 'bonus_m', 'lva', 'dlva', 'reg_share', 'union']].describe().T
    desc = desc.round(3).reset_index().rename(columns={'index': '변수'})
    RESULTS['0_기술통계.csv'] = desc
    if OUT:
        desc.to_csv(os.path.join(OUT, '0_기술통계.csv'), index=False, encoding='utf-8-sig')
    if not QUIET:
        print(desc.to_string(index=False))

    FE1, FE2 = ['indyr'], ['id', 'indyr']
    single, cost_ok = w[w.single], w[w.cost_ok]

    # ---- H7: 임금 → 자발적 이직률 (임금 10%당 %p)
    H7 = dict(y='turn', scale=LN10, bound=BOUND_H7)
    r7 = [
        fe_reg(w, xs=['lw'] + CTRL, fes=FE1, label='★주 검정: 횡단 (ln 급여 + 통제 | 중분류×연도)', **H7),
        fe_reg(w, xs=['lw', 'bonus'] + CTRL, fes=FE1, label='횡단 + 성과배분 동시 투입', **H7),
        fe_reg(w, xs=['lw'], fes=FE1, label='횡단, 통제 없음', **H7),
        fe_reg(w, xs=['lw'] + CTRL, fes=FE2, label='기업 고정효과 (같은 회사의 임금 변화)', **H7),
        fe_reg(w, xs=['lw', 'turn'] + CTRL, fes=FE1, label='시차: 2년 뒤 이직률 (현재 이직률 통제)',
               **{**H7, 'y': 'turn_f'}),
        fe_reg(single, xs=['lw'] + CTRL, fes=FE1, label='견고성: 단독사업장', **H7),
        fe_reg(cost_ok, xs=['lw'] + CTRL, fes=FE1, label='견고성: 제조원가 급여 결측 없음', **H7),
        fe_reg(w, xs=['lw'] + CTRL, fes=FE1, label='견고성: 상하 1% 절단', wins=True, **H7),
        fe_reg(w, xs=['lw', 'sen_share', 'fem_share'] + CTRL, fes=FE1, label='견고성: 근속 20년 이상·여성 비중 통제 (호봉 역방향 점검)', **H7),
        fe_reg(w.assign(turn=w.turn_all), xs=['lw'] + CTRL, fes=FE1, label='대체 결과: 정규직 전체 이직률', **H7),
        fe_reg(w, xs=['wpos'] + CTRL, fes=FE1, y='turn', scale=10, label='대체 원인: 임금 위치 10%p당'),
    ]
    t7 = table(r7, 'H7_임금_이직률.csv')

    # 임금 위치 5분위별 이직률 (같은 업종·연도 평균을 뺀 값)
    q = w.dropna(subset=['wpos', 'turn']).copy()
    q['분위'] = pd.qcut(q.wpos, 5, labels=['1 (가장 낮음)', '2', '3', '4', '5 (가장 높음)'])
    q['이직률_업종연도조정'] = q.turn - q.groupby('indyr').turn.transform('mean') + q.turn.mean()
    qt = q.groupby('분위', observed=True).agg(관측=('turn', 'size'), 임금위치_중앙=('wpos', 'median'),
                                             이직률_평균=('turn', 'mean'), 이직률_중앙=('turn', 'median'),
                                             이직률_업종연도조정=('이직률_업종연도조정', 'mean')).reset_index()
    table(qt.to_dict('records'), 'H7_임금위치_5분위.csv')

    # ---- H8: 성과배분 → 생산성 (2년 뒤 Δln 1인당 부가가치, %)
    H8 = dict(y='dlva', scale=1.0, bound=BOUND_H8)
    r8 = [
        fe_reg(w, xs=['bonus', 'lva'] + CTRL, fes=FE1, label='★주 검정: 시차 (성과배분_t → Δln 부가가치 t→t+2)', **H8),
        fe_reg(w, xs=['bonus', 'lva', 'lw'] + CTRL, fes=FE1, label='시차 + 임금 동시 투입', **H8),
        fe_reg(w, xs=['bonus', 'lva'], fes=FE1, label='시차, 통제 없음', **H8),
        fe_reg(single, xs=['bonus', 'lva'] + CTRL, fes=FE1, label='견고성: 단독사업장', **H8),
        fe_reg(cost_ok, xs=['bonus', 'lva'] + CTRL, fes=FE1, label='견고성: 제조원가 급여 결측 없음', **H8),
        fe_reg(w, xs=['bonus', 'lva'] + CTRL, fes=FE1, label='견고성: 상하 1% 절단', wins=True, **H8),
        fe_reg(w, xs=['bonus_m', 'lva'] + CTRL, fes=FE1, y='dlva', label='대체 원인: 성과배분 수준 1개월분당'),
        fe_reg(w, xs=['bonus', 'lrev'] + CTRL, fes=FE1, y='dlrev', label='대체 결과: Δln 1인당 매출(%)'),
        fe_reg(w, xs=['bonus', 'opm'] + CTRL, fes=FE1, y='dopm', label='대체 결과: Δ영업이익률(%p)'),
        fe_reg(w, xs=['bonus'] + CTRL, fes=FE1, y='lva', label='참고: 같은 해 횡단 (ln 부가가치 수준 차이, 로그×100 아님)', scale=100),
        fe_reg(w, xs=['bonus'] + CTRL, fes=FE2, y='lva', label='참고: 기업 고정효과 (같은 해, ×100)', scale=100),
    ]
    t8 = table(r8, 'H8_성과배분_생산성.csv')

    # H8 추가 점검: 역방향(원래 잘나가던 회사)·기계적 증가(부가가치 안의 인건비)
    new = w[w.bonus_p.eq(0)]                                          # 2년 전 미실시였던 곳
    r8b = [
        fe_reg(w, xs=['bonus', 'lva_p'] + CTRL, fes=FE1, y='dlva_pre', label='사전 추세: 성과배분_t ~ Δln 부가가치 t−2→t (위약 검정)'),
        fe_reg(new, xs=['bonus', 'lva'] + CTRL, fes=FE1, y='dlva', label='신규 도입: 2년 전 미실시 중 올해 실시 vs 계속 미실시'),
        fe_reg(new, xs=['bonus', 'lva_p'] + CTRL, fes=FE1, y='dlva_pre', label='신규 도입의 사전 추세 (t−2→t)'),
        fe_reg(w, xs=['bonus', 'bonus_f', 'lva'] + CTRL, fes=FE1, y='dlva', label='2년 뒤 실시 여부 통제'),
        fe_reg(w, xs=['bonus', 'lva'] + CTRL, fes=FE1, y='dva_lab', wins=True, label='분해: 부가가치 변화 중 인건비 부분(t년 부가가치 대비 %)'),
        fe_reg(w, xs=['bonus', 'lva'] + CTRL, fes=FE1, y='dva_nonlab', wins=True, label='분해: 인건비를 뺀 나머지 부분(영업이익·감가 등, %)'),
    ]
    table(r8b, 'H8_추가점검.csv')

    # ---- 교차 (탐색)
    rx = [
        fe_reg(w, xs=['bonus'] + CTRL, fes=FE1, y='turn', label='H7b 성과배분 → 이직률(%p), 횡단'),
        fe_reg(w, xs=['bonus', 'lw'] + CTRL, fes=FE1, y='turn', label='H7b 성과배분 → 이직률, 임금 통제'),
        fe_reg(w, xs=['bonus'] + CTRL, fes=FE2, y='turn', label='H7b 성과배분 → 이직률, 기업 FE'),
        fe_reg(w, xs=['lw', 'lva'] + CTRL, fes=FE1, y='dlva', scale=LN10, label='H8b 임금 10%당 → Δln 부가가치(%), 시차'),
        fe_reg(w, xs=['lw', 'bonus', 'lva'] + CTRL, fes=FE1, y='dlva', scale=LN10, label='H8b 임금 → Δln 부가가치, 성과배분 통제'),
    ]
    table(rx, 'H7b_H8b_교차.csv')

    # ---- 주 검정 요약 + Holm
    main_rows = [dict(가설='H7 임금 → 자발적 이직률', 단위='임금 10%당 %p', 경계=f'±{BOUND_H7}', **{k: t7.iloc[0][k] for k in t7.columns if k != '모형'}),
                 dict(가설='H8 성과배분 → 2년 뒤 생산성', 단위='%', 경계=f'±{BOUND_H8}', **{k: t8.iloc[0][k] for k in t8.columns if k != '모형'})]
    s = pd.DataFrame(main_rows)
    s['p_holm(효과=0)'] = holm(s['p(효과=0)'])
    s['TOST p_holm'] = holm(s['TOST p'])
    table(s.to_dict('records'), 'H7_H8_주검정요약.csv')

    # ---- DART 보조: 평균근속연수 (DART 파일이 있을 때만)
    if dart:
        dart_tenure()
    return dict(RESULTS)


def dart_tenure():
    P = os.path.join(DATA, 'DART_패널', 'DART_패널_2015_2025.csv')
    E = os.path.join(DATA, '산술식_재검토', '결과', '_emp.pkl')
    if not (os.path.exists(P) and os.path.exists(E)):
        if not QUIET:
            print('DART 보조 생략(파일 없음)')
        return
    p = pd.read_csv(P, dtype={'기업고유코드': str})
    p = p[~p['플래그_지주회사'].astype(bool) & ~p['플래그_급여이상'].astype(bool) & ~p['플래그_직원10명미만'].astype(bool)]
    p = p[p['직원수'].ge(10) & p['급여총액(원)'].gt(0)].copy()
    e = pd.read_pickle(E)[['id', 'yr', 'ten']]
    e['id'] = e['id'].astype(str)
    d = p.merge(e, left_on=['기업고유코드', '사업연도'], right_on=['id', 'yr'], how='inner')
    d = d[d.ten.between(0.3, 45)].copy()
    d['lw'] = np.log(d['급여총액(원)'] / d['직원수'])
    d['lten'] = np.log(d.ten)
    d['lsize'] = np.log(d['직원수'])
    d['indyr'] = d['업종코드_중분류'].astype(str) + '_' + d['사업연도'].astype(str)
    d['id'] = d['기업고유코드']
    rows = [fe_reg(d, y='lten', xs=['lw', 'lsize'], fes=['indyr'], scale=LN10 * 100, label='DART 횡단: 임금 10%당 평균근속연수 변화(%)'),
            fe_reg(d, y='lten', xs=['lw', 'lsize'], fes=['id', 'indyr'], scale=LN10 * 100, label='DART 기업 고정효과')]
    table(rows, 'H7_DART_근속연수.csv')


if __name__ == '__main__':
    arg = sys.argv[1:]
    main(arg[0] if arg else None, out=arg[1] if len(arg) > 1 else os.path.join(HERE, '결과_가설검정_추가'))
