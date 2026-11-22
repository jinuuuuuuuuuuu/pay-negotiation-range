"""산술식 결과 파일 만들기 — formula.py만 사용 (옛 f6_최종계산.py · f7_모든구간.py를 대체)

사용:  python run_산술식.py            → 2023~2025 결과 + 3년 구간 9개 전부
       python run_산술식.py 2018 2022  → 한 구간만 (산술식결과_2018_2022.csv)
경로는 아래 [경로]만 바꾸면 됩니다. 현금흐름·공시 평균급여·WPS 파일이 없으면 그 열만 비고 나머지는 그대로 나옵니다.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import formula as F  # noqa: E402

# [경로]
DATA = os.environ.get('HR_DATA_DIR', os.path.join(os.path.expanduser('~'), 'Downloads'))
PANEL = os.path.join(DATA, 'DART_패널', 'DART_패널_2015_2025.csv')
CFO_DIR = os.path.join(DATA, 'DART_재수집_20261114', '연도별_소형내보내기')     # 영업활동현금흐름 (없으면 생략)
EMP_PKL = os.path.join(DATA, '산술식_재검토', '결과', '_emp.pkl')              # 공시 1인 평균급여 (없으면 생략)
WPS_CSV = os.path.join(DATA, 'WPS_통합.csv')                                   # WPS 원자료 (공유 금지, 없으면 생략)
OUT = os.environ.get('HR_OUT_DIR', os.path.join(DATA, '산술식_재검토', '결과_formula'))

CHECK = ['삼성전자', 'SK하이닉스', '현대자동차', '기아', 'LG전자', 'NAVER', '카카오', '셀트리온', '한화오션', 'HD현대중공업',
         'LG유플러스', '삼성SDI', '포스코퓨처엠', '오뚜기', '한미반도체', '에코프로비엠', '현대모비스', '이마트']


def save(df, name):
    df.to_csv(os.path.join(OUT, name), index=False, encoding='utf-8-sig')
    print(f'  → {name} ({len(df):,}행)')


def load_inputs():
    panel = F.load_panel(PANEL)
    cfo = F.load_cfo(CFO_DIR) if os.path.isdir(CFO_DIR) else None
    emp = None
    if os.path.exists(EMP_PKL):
        emp = pd.read_pickle(EMP_PKL)
        emp['id'] = emp['id'].astype(str)
    wps = None
    try:
        wps = F.load_wps(WPS_CSV)
    except FileNotFoundError:
        print('WPS 원자료 없음 → WPS 열은 빈칸')
    return panel, F.build_core(panel, cfo=cfo, emp=emp), wps


def summary_row(B):
    c = B[B['인상 계산'] == '계산']
    r = {'구간': B['구간'].iloc[0], '기업': len(B),
         '두 축 판정(%)': round(((B['임금 위치'] != '비교 불가') & (B['지급 여력'] != '판정 불가')).mean() * 100),
         '비교 불가': int((B['임금 위치'] == '비교 불가').sum())}
    for v in ['임금 높음', '임금 보통', '임금 낮음']:
        r[v] = int((B['임금 위치'] == v).sum())
    for v in ['여력 있음', '여력 보통', '여력 제약']:
        r[v] = int((B['지급 여력'] == v).sum())
    r['한계기업'] = int(B['한계'].sum())
    r['순위상관(임금 vs 이익률)'] = round(B.P.corr(B.opm, method='spearman'), 2)
    r['비교 오차 중앙(%)'] = round((np.exp((np.log(B.w) - np.log(B.ref)).abs().median()) - 1) * 100, 1)
    r['g* 중앙(%)'] = round(c['g*'].median(), 2)
    r['이익률 하락 중앙(%p)'] = round(c['하락'].median(), 2)
    r['이익연동 비율 계산 가능'] = int(B['전환_같은 금액이 되는 영업이익 비율(%)'].notna().sum())
    r['WPS 회차'] = B['WPS_조사회차'].iloc[0]
    return r


def stability(R):
    rows = []
    for s in range(2015, 2021):
        A, B = R[s], R[s + 3]
        j = A.index.intersection(B.index)
        out = {'구간 쌍': f'{s}~{s + 2} → {s + 3}~{s + 5}'}
        for c in ['임금 위치', '지급 여력']:
            x, y = A.loc[j, c], B.loc[j, c]
            ok = ~x.isin(['비교 불가', '판정 불가']) & ~y.isin(['비교 불가', '판정 불가'])
            out[c + ' 유지(%)'] = round((x[ok] == y[ok]).mean() * 100)
        x = A.loc[j, '임금 위치'] + '|' + A.loc[j, '지급 여력']
        y = B.loc[j, '임금 위치'] + '|' + B.loc[j, '지급 여력']
        ok = ~x.str.contains('불가') & ~y.str.contains('불가')
        out['두 축 조합 유지(%)'] = round((x[ok] == y[ok]).mean() * 100)
        out['공통 기업'] = int(ok.sum())
        loss = (B.OP.reindex(A.index) < 0).where(B.OP.reindex(A.index).notna())
        for v in ['여력 제약', '여력 보통', '여력 있음']:
            out[f'"{v}" → 이후 합산 적자(%)'] = round(loss[A['지급 여력'] == v].mean() * 100)
        rows.append(out)
    return pd.DataFrame(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    panel, core, wps = load_inputs()
    print(f'분석 표본: {len(core):,}행 · {core.id.nunique():,}곳')
    if len(sys.argv) == 3:
        a, b = int(sys.argv[1]), int(sys.argv[2])
        save(F.to_table(F.compute(core, a, b, wps=wps)), f'산술식결과_{a}_{b}.csv')
        return
    R = {s: F.compute(core, s, s + 2, wps=wps) for s in range(2015, 2024)}
    B = R[2023]
    t = F.to_table(B)
    save(t, '산술식결과_2023_2025.csv')
    save(pd.concat([F.to_table(R[s]) for s in R]), '산술식결과_모든구간.csv')
    save(pd.DataFrame([summary_row(R[s]) for s in R]), '구간별요약.csv')
    save(stability(R), '구간쌍_안정성.csv')
    peers = B.attrs['peers'].copy()
    peers['기업명'] = peers['id'].map(B['name'])
    peers['비교 기업명'] = peers['peer_id'].map(B['name'])
    peers['비교 기업 중분류'] = peers['peer_id'].map(B['ind2'])
    peers['비교 기업 1인당 급여(만원)'] = (peers['peer_id'].map(B['w']) / 1e4).round(0)
    save(peers[['id', '기업명', '순번', 'peer_id', '비교 기업명', '비교 기업 중분류', '같은 중분류', '거리',
                '비교 기업 1인당 급여(만원)']].round({'거리': 3}), '비교군목록_2023_2025.csv')
    cols = ['기업명', '중분류', '1인당 급여(만원)', '임금 차이(%)', '임금 위치', '비교군 구성', '비교군 주의', '영업이익률(%)',
            '업종 중앙 영업이익률(%)', '업종 기준 단위', '지급 여력', '여력 사유', '현금흐름 표시', '인상5%_영업이익률 하락(%p)',
            '인상5%_비용÷영업이익(%)', '인상5%_g*(%)', 'D 상태(마지막 해)', '전환_같은 금액이 되는 영업이익 비율(%)',
            '급여 확인', '진단문장']
    chk = t[t['기업명'].isin(CHECK)][cols]
    save(chk, '상식점검.csv')
    print('  상식 점검에서 빠진 기업:', [n for n in CHECK if n not in set(chk['기업명'])])
    # 인상 결정·이익연동 전환·스트레스 테스트의 기업별 재료 = MVP 입력
    ctx = F.sim_context(B, core)
    mvp = ctx.firms.reset_index().rename(columns={'index': 'id'})
    save(mvp, 'MVP입력_2023_2025.csv')
    # 기능 4 스트레스 테스트의 업종×연도 충격표 (중분류 / 대분류 / 전체)
    for lvl, t in ctx.shocks.items():
        x = t.reset_index()
        if lvl == '중분류':
            x.insert(1, '중분류명', x['ind2'].map(F.IND2_NAME))
        for col in ['이익률변화', '이익률변화_하위25', '매출변화', '매출변화_하위25']:
            x[col] = (x[col] * 100).round(2)
        x = x.rename(columns={'이익률변화': '영업이익률 변화 중앙(%p)', '이익률변화_하위25': '영업이익률 변화 하위25(%p)',
                              '매출변화': '매출 변화 중앙(%)', '매출변화_하위25': '매출 변화 하위25(%)'})
        save(x, f'업황충격표_{lvl}x연도.csv')
    old = os.path.join(OUT, '업황충격표_중분류.csv')
    if os.path.exists(old):
        os.remove(old)                     # 옛 형식(시나리오 3개만) 파일은 지움
    d = F.clean_depreciation(F.mark_sample(panel))
    save(d[d['감가_비움']][['id', 'name', 'yr', 'DEP', 'REV', '감가상각비_상태']], '감가이상_비운행.csv')
    if wps is not None:
        T, pool = F.wps_table(F.prepare_wps(wps), 2025)
        save(T.assign(조사회차='+'.join(map(str, pool))), 'WPS기준값_대분류x직원구간.csv')


if __name__ == '__main__':
    main()
