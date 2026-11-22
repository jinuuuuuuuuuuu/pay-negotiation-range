"""wps_hypothesis.py 검산 테스트 — 가상 자료로 회귀·고정효과·동등성 검정(TOST)·Holm이 맞게 도는지 본다.
WPS 원자료 없이 돌아간다.   실행:  cd formula  →  python -m pytest tests -q
"""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import wps_hypothesis as WH  # noqa: E402


def panel(n_firms=400, years=(2015, 2017, 2019), beta=-0.5, firm_effect=2.0, seed=1):
    """이직 = beta × (ln 급여 × 10/ln1.1 단위 효과) + 기업 고정효과 + 잡음. 기업 효과가 급여와 상관되게 만든다."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_firms):
        fe = rng.normal(0, 1)
        for y in years:
            lw = 3.8 + 0.5 * fe + rng.normal(0, 0.15)             # 급여는 기업 효과와 양의 상관
            rows.append(dict(id=i, year=y, indyr=f'{i % 8}_{y}', lw=lw,
                             turn=10 + beta / np.log(1.1) * lw + firm_effect * fe + rng.normal(0, 1.0)))
    return pd.DataFrame(rows)


def test_holm_matches_hand_calc():
    p = [0.01, 0.04, 0.03]
    assert np.allclose(WH.holm(p), [0.03, 0.06, 0.06])           # (3·0.01, max(2·0.03, .03), max(1·0.04, .06))
    assert np.allclose(WH.holm([0.5]), [0.5])


def test_fe_reg_recovers_effect_within_firm():
    d = panel()
    within = WH.fe_reg(d, y='turn', xs=['lw'], fes=['id', 'indyr'], scale=np.log(1.1), label='fe')
    assert within['효과'] == pytest.approx(-0.5, abs=0.12)       # 기업 효과를 빼면 참값
    assert within['95% 하한'] < -0.5 < within['95% 상한']
    cross = WH.fe_reg(d, y='turn', xs=['lw'], fes=['indyr'], scale=np.log(1.1), label='cross')
    assert cross['효과'] > within['효과'] + 0.2                  # 기업 효과를 안 빼면 편향(이 가상 자료에서는 약 +0.35)


def test_tost_decision():
    d = panel(firm_effect=0.0)
    small = WH.fe_reg(d, y='turn', xs=['lw'], fes=['indyr'], scale=np.log(1.1), bound=0.8, label='s')
    assert small['TOST p'] < 0.05                                 # 효과 −0.5 → ±0.8 경계 안
    tight = WH.fe_reg(d, y='turn', xs=['lw'], fes=['indyr'], scale=np.log(1.1), bound=0.3, label='t')
    assert tight['TOST p'] > 0.05                                 # ±0.3 경계에는 못 들어감
    assert tight['p(효과=0)'] < 0.001                             # 그래도 효과는 있음


def test_fe_reg_requires_two_obs_for_firm_fe():
    d = panel(n_firms=50, years=(2015,))
    with pytest.raises(Exception):
        WH.fe_reg(d, y='turn', xs=['lw'], fes=['id', 'indyr'], label='x')


def test_prespecified_bounds_are_fixed():
    assert WH.BOUND_H7 == 0.5 and WH.BOUND_H8 == 1.4              # 결과를 본 뒤 바꾸지 않음 (결정표 13장)
