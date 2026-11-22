"""formula.py 검산 테스트.

실행:  cd formula  →  python -m pytest tests -q
- A~E: 손으로 계산할 수 있는 가상 예시 (자료 없이 돌아감). 「보상 프로젝트 완전 이해」 PDF의 A사·B사 숫자와 같음
- F: 실제 패널 2023~2025 결과를 고정한 회귀 테스트. 산술식 최종본·노트북 5-8 대조표 숫자.
     패널이 없으면 건너뜀. 경로는 환경변수 HR_DATA_DIR (기본: 사용자 홈의 Downloads 폴더)
규칙을 일부러 바꿨다면 F의 기대값을 새 숫자로 고치고 결정표 11장에 기록한다.
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import formula as F  # noqa: E402

EOK = 1e8


# ---------------------------------------------------------------------
# A. 비용 계산 (기능 2~4) — 가상 A사: 급여 180억, 매출 1,000억, 영업이익 50억, D 30억
# ---------------------------------------------------------------------
def firm_a(**over):
    row = dict(S_T=180 * EOK, OP_T=50 * EOK, REV_T=1000 * EOK, DEPf_T=30 * EOK, TAX_T=0.0, BAD_T=0.0,
               opm_sd=0.04, **{'지급 여력': '여력 있음'})
    row.update(over)
    return pd.DataFrame([row], index=['A'])


def test_a_cost_numbers():
    r = F.cost(firm_a()).iloc[0]
    assert r.dW == pytest.approx(9.9 * EOK)                 # 180 × 5% × 1.1
    assert r['하락'] == pytest.approx(0.99)                  # 9.9 ÷ 1,000 → 0.99%p
    assert r['비용÷영업이익'] == pytest.approx(19.8)          # 9.9 ÷ 50
    assert r['g*'] == pytest.approx(9.9 / 260 * 100)         # 3.8077%
    assert r['D상태'] == '정식'
    assert r['평소변동대비'] == pytest.approx(0.2475)         # 0.99%p ÷ 4%p


def test_a_d_status_and_gstar_flags():
    assert F.cost(firm_a(TAX_T=np.nan)).iloc[0]['D상태'] == '보완'
    simple = F.cost(firm_a(DEPf_T=np.nan)).iloc[0]
    assert simple['D상태'] == '간이' and simple['g*'] == pytest.approx(9.9 / 230 * 100)   # D 없이 S+OP
    over = F.cost(firm_a(S_T=180 * EOK, OP_T=-170 * EOK, DEPf_T=0.0)).iloc[0]          # 분모 10억 → g* 99%
    assert np.isnan(over['g*']) and over['g*원값'] > 10 and over['g*표시'].startswith('10% 초과')
    neg = F.cost(firm_a(OP_T=-300 * EOK)).iloc[0]                                       # 분모 ≤ 0
    assert np.isnan(neg['g*']) and neg['g*표시'].startswith('계산 불가')
    assert np.isnan(neg['비용÷영업이익'])                                                # 영업적자면 비율 안 냄


def test_a_overhead_and_rate_are_inputs():
    r = F.cost(firm_a(), rate=0.10, c=0.18).iloc[0]
    assert r.dW == pytest.approx(180 * EOK * 0.10 * 1.18)


# ---------------------------------------------------------------------
# B. 평소 변동 — 이익률 10·6·4·4·6·10% → 변화 −4·−2·0·+2·+4%p → 표본 표준편차 √10 ≈ 3.162%p
# ---------------------------------------------------------------------
def test_b_volatility():
    opm = np.array([.10, .06, .04, .04, .06, .10])
    core = pd.DataFrame({'id': 'X', 'yr': range(2015, 2021), 'opm': opm,
                         'dopm': np.r_[np.nan, np.diff(opm)], 'dlw': np.nan})
    v = F.volatility(core, 2020)
    assert v.loc['X', 'opm_sd'] == pytest.approx(np.sqrt(10) / 100)
    assert 'X' not in F.volatility(core, 2019).opm_sd.dropna().index      # 변화값 4개 → 계산 안 함


# ---------------------------------------------------------------------
# C. 이익연동 전환 (기능 3) — 3년 합산 기준 비율. 과거 연도에 적용해 보기는 하지 않음 (11-21)
# ---------------------------------------------------------------------
def test_c_share_rate():
    o = pd.DataFrame({'S': [300 * EOK, 300 * EOK], 'OP': [60 * EOK, -5 * EOK]}, index=['B', 'L'])
    r = F.profit_share_rate(o)
    assert r.loc['B', '전환_같은 금액이 되는 영업이익 비율(%)'] == pytest.approx(25.0)     # 15억 ÷ 60억
    assert np.isnan(r.loc['L', '전환_같은 금액이 되는 영업이익 비율(%)']) and r.loc['L', '전환_표시'] != ''


# ---------------------------------------------------------------------
# D. 비교군과 임금 위치 (기능 1)
# ---------------------------------------------------------------------
def synthetic_window(seed=0):
    """대분류 C: 중분류 10번 30곳 + 11번 5곳 / 대분류 J: 10곳(21곳 미만 → 비교 불가) / 매출 없는 1곳."""
    rng = np.random.default_rng(seed)
    rows = []
    for sec, ind2, n in [('C', 10, 30), ('C', 11, 5), ('J', 58, 10)]:
        for i in range(n):
            rev = np.exp(rng.normal(25, 1))
            rows.append(dict(sec=sec, ind2=ind2, REV=rev, AST=rev * 1.2, N=100 + i, w=5e7 * np.exp(rng.normal(0, .2))))
    rows.append(dict(sec='C', ind2=10, REV=np.nan, AST=np.nan, N=100, w=6e7))
    o = pd.DataFrame(rows, index=[f'f{i}' for i in range(len(rows))])
    o['ok'] = (o.REV > 0) & (o.AST > 0)
    o['lrev'] = np.log(o.REV.where(o.ok))
    o['lk'] = np.log((o.AST / o.N).where(o.ok))
    o['sr'] = 0.1
    return o


def test_d_two_step_peers():
    o, peers = F.wage_position(synthetic_window())
    big = o[(o.ind2 == 10) & o.ok]
    small = o[o.ind2 == 11]
    assert (big.n_same == 20).all()                     # 같은 중분류가 29곳이면 20곳 모두 같은 중분류
    assert (small.n_same == 4).all()                    # 같은 중분류 4곳 + 대분류에서 16곳 채움
    first = peers[peers.id == small.index[0]].sort_values('순번')
    assert first['같은 중분류'].head(4).all() and not first['같은 중분류'].iloc[4:].any()   # 같은 중분류가 먼저
    assert (o.loc[o.sec == 'J', '임금 위치'] == '비교 불가').all()
    assert (o.loc[o.sec == 'J', '비교군 주의'] == '대분류 기업 수 부족(21곳 미만)').all()
    assert o.loc[~o.ok, '비교군 주의'].iloc[0] == '매출·자산 없음'


def test_d_same_as_penalty_rule():
    # 두 단계 선택 = 옛 구현(다른 중분류 거리에 1000을 더하고 가까운 순)과 같은 결과
    o = synthetic_window(seed=3)
    g = o[o.ok & (o.sec == 'C')]
    X = g[['lrev', 'lk']].values
    X = (X - X.mean(0)) / X.std(0)
    dist = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
    iv = g.ind2.to_numpy()
    pen = dist + 1000 * (iv[:, None] != iv[None, :])
    np.fill_diagonal(pen, np.inf)
    for i in range(len(g)):
        assert set(F.select_peers(dist[i], iv, iv[i], exclude=i)) == set(np.argsort(pen[i], kind='stable')[:20])


def test_d_rank_and_label():
    o, _ = F.wage_position(synthetic_window())
    r = o.dropna(subset=['P'])
    assert r.P.between(0, 1).all()
    assert (r.loc[r.P >= .75, '임금 위치'] == '임금 높음').all()
    assert (r.loc[r.P <= .25, '임금 위치'] == '임금 낮음').all()
    assert np.allclose(r['임금 차이(%)'], (r.w / r.ref - 1) * 100)
    assert (r.ref25 <= r.ref).all() and (r.ref <= r.ref75).all()


# ---------------------------------------------------------------------
# E. 지급 여력 (기능 1)
# ---------------------------------------------------------------------
def test_e_pay_capacity_order():
    base = dict(sec='C', ind2=10, CFO=1.0)
    rows = [dict(OP=-1, opm=-0.01, 한계=False),           # 3년 합산 적자 → 제약
            dict(OP=5, opm=0.05, 한계=True),              # 3년 모두 한계 신호 → 제약
            dict(OP=5, opm=np.nan, 한계=False),           # 매출 없음 → 판정 불가
            dict(OP=5, opm=0.09, 한계=False),             # 업종 중앙값 이상 → 있음
            dict(OP=5, opm=0.01, 한계=False)]             # 미만 → 보통
    rows += [dict(OP=5, opm=0.05, 한계=False)] * 10        # 중분류 기업 수를 11곳 이상으로
    o = F.pay_capacity(pd.DataFrame([{**base, **r} for r in rows]))
    assert list(o['지급 여력'][:5]) == ['여력 제약', '여력 제약', '판정 불가', '여력 있음', '여력 보통']
    assert o['업종기준단위'].iloc[0] == '중분류'
    assert o['여력 사유'].iloc[1] == '이자보상비율 3년 연속 1 미만'
    small = F.pay_capacity(pd.DataFrame([{**base, **r} for r in rows[:5]]))   # 중분류 4곳 → 대분류도 4곳 → 전체
    assert small['업종기준단위'].iloc[0] == '전체'


def test_e_cash_flow_flag_does_not_change_grade():
    o = pd.DataFrame([dict(sec='C', ind2=10, OP=5, opm=0.09, 한계=False, CFO=-1.0)]
                     + [dict(sec='C', ind2=10, OP=5, opm=0.05, 한계=False, CFO=1.0)] * 11)
    r = F.pay_capacity(o).iloc[0]
    assert r['지급 여력'] == '여력 있음' and r['현금흐름 표시'] != ''


# ---------------------------------------------------------------------
# F. 실제 자료 회귀 테스트 (2023~2025, 산술식 최종본·노트북 5-8 숫자)
# ---------------------------------------------------------------------
DATA = os.environ.get('HR_DATA_DIR', os.path.join(os.path.expanduser('~'), 'Downloads'))
PANEL = os.path.join(DATA, 'DART_패널', 'DART_패널_2015_2025.csv')
EXPECT_ALPHA_MEDIAN = 8.133   # 2023~25, 급여 5%와 같은 금액이 되는 영업이익 비율 중앙값(3년 합산, 1,411곳)


@pytest.fixture(scope='module')
def real():
    if not os.path.exists(PANEL):
        pytest.skip('패널 파일 없음')
    core = F.build_core(F.load_panel(PANEL))
    return core, F.compute(core, 2023, 2025)


def test_f_sample(real):
    core, r = real
    assert (len(core), core.id.nunique()) == (21761, 2840)
    assert len(r) == 2205


def test_f_two_axes(real):
    _, r = real
    assert r['임금 위치'].value_counts().to_dict() == {'임금 보통': 884, '임금 높음': 653, '임금 낮음': 554, '비교 불가': 114}
    assert r['지급 여력'].value_counts().to_dict() == {'여력 있음': 1043, '여력 제약': 827, '여력 보통': 309, '판정 불가': 26}
    assert (r['비교군 주의'] == '대분류 기업 수 부족(21곳 미만)').sum() == 44
    j = r.n_same.notna()
    assert round((r.n_same[j] / 20).mean() * 100) == 96 and (r.n_same[j] < 20).sum() == 208
    assert r['업종기준단위'].value_counts().to_dict() == {'중분류': 2080, '대분류': 79, '전체': 46}


def test_f_cost_medians(real):
    _, r = real
    c = r[r['인상 계산'] == '계산']
    assert len(c) == 1378
    assert c['하락'].median() == pytest.approx(0.586, abs=1e-3)
    assert c['비용÷영업이익'].median() == pytest.approx(8.118, abs=1e-3)
    assert c['g*'].median() == pytest.approx(2.846, abs=1e-3)


def test_f_profit_share(real):
    _, r = real
    a = r['전환_같은 금액이 되는 영업이익 비율(%)']
    assert a.notna().sum() == int((r.OP > 0).sum())
    assert a.median() == pytest.approx(EXPECT_ALPHA_MEDIAN, abs=1e-3)


@pytest.mark.parametrize('name, gap, label, cap, opm_ind', [
    ('현대자동차', 34.32, '임금 높음', '여력 있음', 3.55),
    ('오뚜기', -18.98, '임금 낮음', '여력 있음', 3.32),
    ('LG유플러스', 25.21, '임금 보통', '여력 있음', 5.66),
    ('HD현대중공업', 65.5, '임금 높음', '여력 보통', 6.9),     # 옛 제조 4군에서는 −9.6%·여력 있음(업종 기준 3%)
])
def test_f_firms(real, name, gap, label, cap, opm_ind):
    _, r = real
    x = r[r.name == name].iloc[0]
    assert x['임금 차이(%)'] == pytest.approx(gap, abs=0.05)
    assert x['임금 위치'] == label and x['지급 여력'] == cap
    assert x.opm_ind * 100 == pytest.approx(opm_ind, abs=0.05)


# ---------------------------------------------------------------------
# G. 인사팀 기능 (7단계) — 가상 A사 + 비교군 4곳
# ---------------------------------------------------------------------
def ctx_a(**over):
    from types import SimpleNamespace
    row = dict(name='A', ind2=10, sec='C', S_T=180 * EOK, N_T=400.0, OP_T=50 * EOK, REV_T=1000 * EOK, D_T=30 * EOK,
               opm_sd=0.04, opm=0.05, sr=0.18, sr_ref=0.15, w=4500e4, w_T=4500e4, **{'지급 여력': '여력 있음'},
               **{'비교군 인상률': 0.04, 'α*': 0.20, '기준연도 업종 충격': False,
                  'S_avg': 180 * EOK, 'OP_avg': 50 * EOK, 'REV_avg': 1000 * EOK, 'N_avg': 400.0,
                  '비교군 이익÷급여': 0.25})
    row.update(over)
    return SimpleNamespace(firms=pd.DataFrame([row], index=['A']),
                           peer_w={'A': np.array([4000e4, 4300e4, 4600e4, 5000e4])}, end=2025,
                           shocks=shocks_a(), catalog=catalog_a())


def shocks_a():
    """가상 충격표: 중분류 10 (2019년은 2곳뿐 → 대분류 C로), 대분류 C, 전체."""
    cols = ['기업수', '이익률변화', '이익률변화_하위25', '매출변화', '매출변화_하위25']
    t2 = pd.DataFrame([(10, 2019, 2, -0.20, -0.30, -0.50, -0.60), (10, 2020, 5, -0.06, -0.10, -0.10, -0.20),
                       (10, 2022, 5, 0.01, -0.01, 0.05, 0.00), (10, 2023, 6, -0.08, -0.15, -0.05, -0.15),
                       (10, 2025, 6, -0.03, -0.05, -0.02, -0.04)],
                      columns=['ind2', 'yr'] + cols).set_index(['ind2', 'yr'])
    t2['평소대비z'] = [np.nan, -1.2, 0.5, -1.6, -0.3]
    t2['큰충격'] = [False, True, False, True, False]
    t1 = pd.DataFrame([('C', 2019, 40, -0.02, -0.05, 0.00, -0.05)], columns=['sec', 'yr'] + cols).set_index(['sec', 'yr'])
    t0 = pd.DataFrame([(2019, 900, -0.005, -0.03, 0.01, -0.04)], columns=['yr'] + cols).set_index('yr')
    return {'중분류': t2, '대분류': t1, '전체': t0}


def catalog_a():
    return pd.DataFrame([
        dict(사건ID='E1', 사건명='가상 사건', 연도=2023, 중분류코드='10', 확인수준='확인', **{'기능4 선택지': '이름 붙여 제공'}),
        dict(사건ID='E2', 사건명='가상 일부근거 사건', 연도=2019, 중분류코드='10', 확인수준='부분확인', **{'기능4 선택지': '이름 붙여 제공 (일부 근거)'}),
        dict(사건ID='E3', 사건명='기준 연도 사건', 연도=2025, 중분류코드='10', 확인수준='확인', **{'기능4 선택지': '제외(기준 연도와 같은 해)'}),
        dict(사건ID='E4', 사건명='공통 후보', 연도=2018, 중분류코드='전체', 확인수준='부분확인', **{'기능4 선택지': '공통 시나리오 후보'}),
        dict(사건ID='X1', 사건명='(원인 미확인) 다른 업종', 연도=2021, 중분류코드='99', 확인수준='원인 미확인', **{'기능4 선택지': '제외(원인 미확인)'}),
    ])


def test_g_overhead_constants():
    assert F.OVERHEAD_C_BASE == pytest.approx(F.OVERHEAD_C + 1 / 12)    # 기본급 = 4대보험 + 퇴직금 적립


def test_g_raise_cost():
    r = F.pay_plan(ctx_a(), 'A', base_raise=0.05, bonus=0.05)
    assert r['그중 기본급 인상분'] == pytest.approx(9 * EOK * (1 + F.OVERHEAD_C_BASE))
    assert r['그중 성과급분'] == pytest.approx(180 * 1.05 * 0.05 * 1.1 * EOK)         # 성과급은 바뀐 급여 기준
    assert r['그중 인원분'] == 0
    assert r['3년 누적 부담(인원·기본급 유지 + 성과급 1회)'] == pytest.approx(3 * r['그중 기본급 인상분'] + r['그중 성과급분'])
    assert r['영업이익률 하락(%p)'] == pytest.approx(r['회사 부담 증가(1년)'] / (1000 * EOK) * 100)
    only_bonus = F.pay_plan(ctx_a(), 'A', bonus=0.05)
    assert only_bonus['회사 부담 증가(1년)'] == pytest.approx(F.cost(firm_a()).iloc[0].dW)   # 기존 비용 계산과 같음
    assert only_bonus['g*(%)'] == pytest.approx(9.9 / 260 * 100)
    assert only_bonus['지급 후 영업이익(내년)'] == pytest.approx(40.1 * EOK)


def test_g_position_with_peer_raise():
    r0 = F.pay_plan(ctx_a(), 'A', base_raise=0.03, peer_raise=0.0)       # 남이 안 올림
    r1 = F.pay_plan(ctx_a(), 'A', base_raise=0.03)                        # 비교군 최근 증가율 4%
    assert r0['지금 순위(마지막 해)'] == pytest.approx(0.5)                # 4,500만 원 = 4곳 중 2곳보다 높음
    assert r0['내년 예상 순위'] == pytest.approx(0.75)                    # 4,635만 원 → 4,600보다 높아져 4곳 중 3곳 위
    assert r1['내년 예상 순위'] == pytest.approx(0.5)                     # 비교군도 4% 오르면(4,784만 원) 순위 그대로
    assert r1['비교군 인상률 가정'] == 0.04
    assert r1['내년 예상 임금 차이(%)'] < r0['내년 예상 임금 차이(%)']
    assert r0['지금 임금 차이(%)'] == pytest.approx((4500 / 4450 - 1) * 100)
    assert F.pay_plan(ctx_a(), 'A', base_raise=0.03, headcount=0.1)['내년 1인당 급여'] == pytest.approx(4500e4 * 1.03)


def test_g_loss_flag_and_no_shock_inputs():
    loss = F.pay_plan(ctx_a(OP_T=5 * EOK), 'A', base_raise=0.05)
    assert loss['지급 때문에 적자 전환']
    import inspect                                                        # 업황은 기능 4에서만 (11-21 결정)
    assert 'shock' not in inspect.signature(F.pay_plan).parameters
    assert 'shock' not in inspect.signature(F.profit_link_plan).parameters


def test_g_compare_offers():
    t = F.compare_offers(ctx_a(), 'A', dict(base_raise=0.07), dict(base_raise=0.04, bonus=0.01), headcount=0.02)
    d = t['차이(노조안 − 회사안)']
    assert d['회사 부담 증가(1년)'] == pytest.approx(t.loc['회사 부담 증가(1년)', '노조안'] - t.loc['회사 부담 증가(1년)', '회사안'])
    assert t.loc['인원 증감', '노조안'] == t.loc['인원 증감', '회사안'] == 0.02      # 계획은 두 안에 똑같이
    assert pd.isna(d['지급 때문에 적자 전환'])


def test_g_budget():
    b = F.pay_plan(ctx_a(), 'A', headcount=0.10, base_raise=0.05, bonus=0.02, sales_growth=0.10)
    s1 = 180 * 1.1 * 1.05
    assert b['내년 급여총액(성과급 포함)'] == pytest.approx(s1 * 1.02 * EOK)
    extra = (s1 - 180) * (1 + F.OVERHEAD_C_BASE) + s1 * 0.02 * (1 + F.OVERHEAD_C)
    assert b['회사 부담 증가(1년)'] == pytest.approx(extra * EOK)
    assert b['그중 인원분'] + b['그중 기본급 인상분'] == pytest.approx((s1 - 180) * (1 + F.OVERHEAD_C_BASE) * EOK)
    assert b['지급 후 영업이익(내년)'] == pytest.approx((50 + 100 * 0.05 - extra) * EOK)   # 늘어난 매출 100억에 지금 이익률 5%
    assert b['내년 직원수'] == pytest.approx(440)


def test_g_plan_without_plan_inputs_equals_simple():
    # 인원·매출 0%면 '올해 숫자에 인상안을 넣은 것'과 같음
    p = F.pay_plan(ctx_a(), 'A', base_raise=0.03)
    assert p['지급 전 영업이익(내년)'] == pytest.approx(50 * EOK)
    assert p['회사 부담 증가(1년)'] == pytest.approx(180 * 0.03 * (1 + F.OVERHEAD_C_BASE) * EOK)


def test_g_profit_link_plan():
    p = F.profit_link_plan(ctx_a(), 'A')                                   # α* = 20%, 3년 연평균 영업이익 50억
    assert p['연동 지급'] == pytest.approx(10 * EOK) and p['고정 지급(급여 대비 rate)'] == pytest.approx(9 * EOK)
    assert p['연동 부담 ÷ 영업이익(%)'] == pytest.approx(20 * 1.1)          # α(1 + c): 어느 회사나 같음
    assert p['급여 대비 지급률(%)'] == pytest.approx(10 / 180 * 100)      # 회사마다 다른 것은 직원 몫
    assert F.profit_link_plan(ctx_a(), 'A', alpha=0.30, cap=0.05)['연동 지급'] == pytest.approx(9 * EOK)   # 15억 → 상한 9억
    assert F.profit_link_plan(ctx_a(OP_avg=45 * EOK, **{'α*': 0.2}), 'A', alpha=0.20)['연동 ÷ 고정'] == pytest.approx(1.0)  # 시작값이면 1배
    z = F.profit_link_plan(ctx_a(OP_avg=-5 * EOK), 'A')
    assert z['연동 지급'] == 0 and z['0원 지급']
    assert F.profit_link_plan(ctx_a(OP_avg=-5 * EOK), 'A', floor=0.01)['연동 지급'] == pytest.approx(1.8 * EOK)


def test_g_real_shocks(real):
    core, r = real
    cat_path = os.path.join(DATA, '산술식_재검토', '결과_formula', '사건카탈로그.csv')
    ctx = F.sim_context(r, core, catalog=F.load_catalog(cat_path) if os.path.exists(cat_path) else None)
    f = ctx.firms
    air = F.firm_shock(ctx.shocks, 51, 'H', 2020)
    assert air['이익률변화'] < -0.2 and air['단위'] == '중분류'                  # 항공 2020: 중앙 −30%p
    assert air['매출변화'] < -0.4                                                # 매출도 −55%
    semi = F.firm_shock(ctx.shocks, 26, 'C', 2023)
    assert semi['이익률변화'] == pytest.approx(-0.0342, abs=5e-4)                # 사건카탈로그 E12와 같은 값
    assert f['비교군 인상률'].median() == pytest.approx(0.038, abs=0.003)
    if ctx.catalog is not None:
        hy = f.index[f.name == 'SK하이닉스'][0]
        names = [s['경우'] for s in F.scenarios(ctx, hy)]
        assert any('반도체 메모리 다운사이클 (2023)' in n and '최악의 해' in n for n in names)   # 같은 해는 한 줄로
        hmm = f.index[f.name == 'HMM'][0]
        assert not any('2025' in s['경우'] for s in F.scenarios(ctx, hmm))      # 기준 연도 사건 제외
        assert '기준 연도 경고' in F.stress_test(ctx, hmm).attrs                 # 2025년이 이미 해운 충격 해


# ---------------------------------------------------------------------
# H. 예측 결합 (기능 4-3) — 가상 A사 + 가상 예측
# ---------------------------------------------------------------------
def fc_a(target=True):
    return pd.DataFrame([{'다음해_적자확률': 0.12, '범위예측_대상': target,
                          '영업이익률_P10': 0.005, '영업이익률_P50': 0.04, '영업이익률_P90': 0.07,
                          '매출 성장_P10': np.log(0.95), '매출 성장_P50': np.log(1.05), '매출 성장_P90': np.log(1.15)}],
                        index=['A'])


def test_h_forecast_cases():
    t = F.pay_plan_forecast(ctx_a(), 'A', fc_a(), base_raise=0.05)
    dW = 180 * 0.05 * (1 + F.OVERHEAD_C_BASE) * EOK                         # 10.65억
    assert t.attrs['적용 매출 증가율'] == pytest.approx(0.05)               # 모델 매출 성장 P50
    assert np.allclose(t['회사 부담 증가'], dW)
    assert t.loc['중앙(P50)', '지급 전 영업이익'] == pytest.approx(1050 * EOK * 0.04)    # 42억
    assert t.loc['나쁜 쪽(P10)', '지급 때문에 적자 전환']                     # 5.25억 − 10.65억 < 0
    assert not t.loc['중앙(P50)', '지급 후 적자']
    assert t.attrs['다음 해 적자 확률'] == 0.12
    assert t.attrs['매출 증가율 범위(P10~P90)'] == pytest.approx((-0.05, 0.15))


def test_h_forecast_user_sales_and_not_target():
    t = F.pay_plan_forecast(ctx_a(), 'A', fc_a(), bonus=0.05, sales_growth=0.0)
    assert t.loc['중앙(P50)', '내년 매출'] == pytest.approx(1000 * EOK)
    empty = F.pay_plan_forecast(ctx_a(), 'A', fc_a(target=False), base_raise=0.05)
    assert empty.empty and empty.attrs['다음 해 적자 확률'] == 0.12


# ---------------------------------------------------------------------
# I. 기능 4 스트레스 테스트 — 업황 충격은 여기에만 (11-21 결정)
# ---------------------------------------------------------------------
def test_i_firm_shock_fallback_and_severity():
    sh = shocks_a()
    assert F.firm_shock(sh, 10, 'C', 2020)['단위'] == '중분류'
    fb = F.firm_shock(sh, 10, 'C', 2019)                                    # 중분류 2곳 → 대분류
    assert fb['단위'] == '대분류' and fb['이익률변화'] == pytest.approx(-0.02)
    assert F.firm_shock(sh, 10, 'C', 2020, severity='하위25')['이익률변화'] == pytest.approx(-0.10)
    assert F.firm_shock(sh, 77, 'Z', 2019)['단위'] == '전체'


def test_i_scenarios_rules():
    sc = F.scenarios(ctx_a(), 'A')
    names = [s['경우'] for s in sc]
    assert '코로나형 (2020)' in names and '원자재·금리형 (2022)' in names
    assert '공통 후보 (2018)' in names                                       # 공통 시나리오 후보
    assert '가상 일부근거 사건 (2019) (일부 근거)' in names                   # 부분확인은 표시
    assert not any('기준 연도 사건' in n or '다른 업종' in n for n in names)   # 기준 연도·원인 미확인·다른 업종 제외
    assert '가상 사건 (2023) · 우리 업종 최악의 해' in names                 # 최악의 해(2023, −8%p)와 같은 해 → 한 줄
    assert not any(n.startswith('우리 업종 최악의 해') for n in names)


def test_i_stress_numbers():
    t = F.stress_test(ctx_a(), 'A', base_raise=0.05, alpha=0.20)
    base = F.pay_plan(ctx_a(), 'A', base_raise=0.05)
    assert t.loc['평상시', '지급 후 영업이익'] == pytest.approx(base['지급 후 영업이익(내년)'])
    assert t.loc['평상시', '이익연동 ÷ 고정'] == pytest.approx(10 / 9)
    r = t.loc['코로나형 (2020)']                                            # 이익률 −6%p, 매출 −10%
    assert r['내년 매출'] == pytest.approx(900 * EOK)
    assert r['지급 전 영업이익'] == pytest.approx(900 * (0.05 - 0.06) * EOK)  # −9억
    assert r['지급 후 적자'] and not r['지급 때문에 적자 전환']                # 원래도 적자
    assert r['이익연동 지급'] == 0
    w = t.loc['원자재·금리형 (2022)']                                         # 그해 업종은 오히려 좋아짐
    assert w['지급 전 영업이익'] == pytest.approx(1050 * 0.06 * EOK)


def test_i_stress_options():
    no_sales = F.stress_test(ctx_a(), 'A', base_raise=0.05, with_sales=False)
    assert no_sales.loc['코로나형 (2020)', '내년 매출'] == pytest.approx(1000 * EOK)
    hard = F.stress_test(ctx_a(), 'A', base_raise=0.05, severity='하위25')
    assert hard.loc['코로나형 (2020)', '영업이익률 변화(%p)'] == pytest.approx(-10)
    cu = F.stress_test(ctx_a(), 'A', custom={'이익률': -0.02, '매출': -0.05}).loc['직접 입력']
    assert cu['지급 전 영업이익'] == pytest.approx(950 * 0.03 * EOK)
    warn = F.stress_test(ctx_a(**{'기준연도 업종 충격': True}), 'A')
    assert '기준 연도 경고' in warn.attrs


def test_i_stress_with_forecast():
    t = F.stress_test(ctx_a(), 'A', fc=fc_a(), base_raise=0.05)
    assert t.loc['모델 나쁜 쪽(P10)', '지급 전 영업이익'] == pytest.approx(1050 * 0.005 * EOK)
    assert t.loc['모델 나쁜 쪽(P10)', '지급 때문에 적자 전환']
    assert t.attrs['다음 해 적자 확률'] == 0.12


# ---------------------------------------------------------------------
# J. 기능 2 인상안 협상 구간 — 하한(업계 인상률)~상한(업계와 같은 부담 수준), 11-22 결정
#    가상 A사: 업계 인상률 4%, 우리 이익÷급여 = 50/180 = 0.2778, 비교군 0.25
# ---------------------------------------------------------------------
def test_j_range_hand_numbers():
    r = F.negotiation_range(ctx_a(), 'A')
    assert r['하한'] == pytest.approx(0.04)
    assert r['상한'] == pytest.approx(0.04 * (50 / 180) / 0.25)          # 4.44%
    assert r['상한 상태'] == '계산' and r['상한 표시'] == '4.4%'
    assert r['구간 해석'].startswith('업계 수준 이상도')
    # 상한 = 비용÷영업이익을 비교군과 같게 만드는 인상률 (c′ 약분)
    cb = F.OVERHEAD_C_BASE
    ours = r['상한'] * 180 * (1 + cb) / 50
    peer = 0.04 * (1 + cb) / 0.25
    assert ours == pytest.approx(peer)


def test_j_range_inverted_and_hold():
    inv = F.negotiation_range(ctx_a(**{'비교군 이익÷급여': 0.5}), 'A')        # 비교군이 이익 체력 2배
    assert inv['상한'] == pytest.approx(0.04 * (50 / 180) / 0.5) and inv['상한'] < inv['하한']
    assert '이익연동 전환 검토' in inv['구간 해석']
    hold = F.negotiation_range(ctx_a(**{'비교군 이익÷급여': -0.1}), 'A')       # 비교군 대부분 적자
    assert np.isnan(hold['상한']) and hold['상한 표시'] == '업계 적자로 인한 상한 산출 보류'
    assert hold['하한'] == pytest.approx(0.04)
    loss = F.negotiation_range(ctx_a(OP_avg=-5 * EOK), 'A')                  # 우리 3년 합산 적자
    assert loss['상한'] == 0 and loss['상한 상태'] == '3년 합산 영업적자'


def test_j_range_cap_display_override():
    cap = F.negotiation_range(ctx_a(OP_T=1 * EOK), 'A')                      # 마지막 해 이익이 작음
    assert cap['상한'] == pytest.approx(1 / (180 * (1 + F.OVERHEAD_C_BASE)))
    assert cap['상한 상태'] == '적자 전환 직전에서 제한'
    big = F.negotiation_range(ctx_a(**{'비교군 이익÷급여': 0.05}), 'A')        # 상한 22% → 표시 한도
    assert big['상한'] == pytest.approx(0.2222, abs=1e-3) and big['상한 표시'] == '10% 초과'
    own = F.negotiation_range(ctx_a(), 'A', peer_raise=0.06)                 # 업계 인상률 직접 입력
    assert own['하한'] == 0.06 and own['상한'] == pytest.approx(0.06 * (50 / 180) / 0.25)


def test_j_range_position_rules():
    r = F.negotiation_range(ctx_a(), 'A')                                    # 4.0% ~ 4.44%
    assert [F.range_position(x, r) for x in (0.03, 0.042, 0.05)] == ['하한 미달', '구간 안', '상한 초과']
    inv = F.negotiation_range(ctx_a(**{'비교군 이익÷급여': 0.5}), 'A')        # 상한 2.2% < 하한 4%
    assert [F.range_position(x, inv) for x in (0.02, 0.03, 0.05)] == ['상한 이하', '상한 초과·하한 미달', '하한 이상·상한 초과']
    big = F.negotiation_range(ctx_a(**{'비교군 이익÷급여': 0.05}), 'A')
    assert F.range_position(0.15, big) == '구간 안 (상한 10% 초과)' and F.range_position(0.03, big) == '하한 미달'
    hold = F.negotiation_range(ctx_a(**{'비교군 이익÷급여': -0.1}), 'A')
    assert F.range_position(0.05, hold) == '하한 이상 (상한 산출 보류)'


def test_j_compare_offers_shows_position():
    t = F.compare_offers(ctx_a(), 'A', union=dict(base_raise=0.08), company=dict(base_raise=0.03))
    assert t.loc['구간 위치', '노조안'] == '상한 초과' and t.loc['구간 위치', '회사안'] == '하한 미달'
    assert t.loc['협상 구간 상한', '노조안'] == '4.4%'


def test_j_real_range(real):
    """실제 2023~2025 (2,205곳) 협상 구간 상태 분포 — 결정표 14장 숫자."""
    core, r = real
    f = F.sim_context(r, core).firms
    vc = f['상한 상태'].value_counts().to_dict()
    assert vc == {'계산': 1065, '업계 적자로 인한 상한 산출 보류': 446, '3년 합산 영업적자': 436,
                  '적자 전환 직전에서 제한': 144, '비교군 인상률 없음': 114}
    ok = f['상한'].notna() & f['하한'].notna()
    assert int((f.loc[ok, '상한'] >= f.loc[ok, '하한']).sum()) == 767
    assert int((f.loc[ok, '상한'] > F.RANGE_UPPER_SHOW_MAX).sum()) == 325
