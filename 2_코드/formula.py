"""HR 학술제 산술식 — 단일 정의

이 파일 하나가 산술식의 기준입니다. 결정표.md의 '채택' 열을 그대로 코드로 옮겼고,
노트북(EDA·가설검정·모델링)·MVP·문서는 모두 이 파일을 불러다 씁니다.

- 상수는 맨 위 [상수] 블록에만 둡니다. 다른 곳에서 숫자를 새로 쓰지 않습니다.
- 경로는 이 파일에 고정하지 않습니다. 읽는 함수에 경로를 넘깁니다.
- 기능: 1 진단(임금 위치·지급 여력) / 2 인상 결정(비용·g*·평소 변동 대비·위치, 노조안 비교) / 3 이익연동 전환 / 4 미래 위험(예측 결합)
- '과거 연도에 적용해 보기'(옛 과거 적용)는 쓰지 않음 (11-21 결정)

사용 예:
    import formula as F
    panel = F.load_panel(r'...\\DART_패널_2015_2025.csv')
    core  = F.build_core(panel, cfo=F.load_cfo(r'...\\연도별_소형내보내기'), emp=emp)
    res   = F.compute(core, 2023, 2025, wps=F.load_wps(r'...\\WPS_통합.csv'))
    table = F.to_table(res)                 # 결과 표 (한글 열 이름)
    peers = res.attrs['peers']              # 비교군 20곳 목록 (긴 형식)
"""
import glob
import os
import unicodedata

import numpy as np
import pandas as pd

# =====================================================================
# [상수] 결정표 10장. 숫자를 바꿀 때는 여기만 바꾸고 결정표에 출처를 적는다.
# =====================================================================
YEARS_IN_WINDOW = 3            # 진단 구간 길이 (문서 0장, 가설검정 H4)
MIN_EMPLOYEES = 10             # 분석 표본 직원 하한 (common.py)
UNIT_LIMIT = {'N': 30, 'S': 30, 'AST': 30, 'REV': 100}   # 같은 기업 중앙값 대비 단위 이상 배수 (common.py)
UNIT_MIN_OBS = 3               # 단위 이상 판정에 필요한 관측 연수
OP_TO_ASSET_LIMIT = 3          # |영업이익| > 3 × 자산이면 추출 오류 의심
FINANCE_IND2 = (64, 66)        # 금융·보험 중분류: 제외 (문서 0장 '대상')
FLAGS = ['플래그_지주회사', '플래그_급여이상', '플래그_직원10명미만', '공시접수검토']   # 패널 플래그 4종
DEP_LIMIT = 5                  # 감가상각비 이상값: 같은 기업 양수 중앙값 대비 배수 (문서 0장, 팀원)
DEP_MIN_OBS = 3                # 감가 중앙값을 믿을 최소 양수 관측 연수

PEER_COUNT = 20                # 비교군 수 (문서 1장, k 검수)
HIGH_P, LOW_P = 0.75, 0.25     # 임금 높음 / 낮음 경계 (문서 2-2)
REF_BAND = (25, 75)            # 참고 임금 구간 백분위 (문서 2-2)
SIZE_GAP = 3                   # 비교군 매출 중앙값이 내 매출의 1/3 미만 또는 3배 초과면 경고
INDUSTRY_MIN_FIRMS = 11        # 업종 영업이익률 중앙값에 필요한 최소 기업 수 (문서 2-3)

PAY_RATE = 0.05                # 예시 지급률: 급여의 5% (문서 2-5)
OVERHEAD_C = 0.10              # c: 성과급(일시금)에 붙는 4대보험 회사 부담 (가정). 2026년 법정 합계는 약 11.5%이나
                               #    고연봉 기업은 국민연금 소득 상한으로 실제 부담이 낮아 0.10 사용 (결정표 9-⑮)
RETIREMENT_ACCRUAL = 1 / 12    # 퇴직금 적립: 1년 근속마다 30일분 평균임금 ≈ 급여의 1/12
OVERHEAD_C_BASE = OVERHEAD_C + RETIREMENT_ACCRUAL   # c′: 기본급 인상에 붙는 4대보험 + 퇴직금 ≈ 0.183
PEER_GROWTH_YEARS = 3          # 비교군 인상률: 최근 3년 1인당 급여 연 증가율의 중앙값
SHOCK_COMMON = {'코로나형': 2020, '원자재·금리형': 2022}   # 전 업종 공통 시나리오(각 업종이 그해 실제로 겪은 변화를 적용)
SHOCK_MIN_FIRMS = 3            # 업황 충격의 업종 단위 최소 기업 수. 11곳·5곳이면 항공(2020년 4곳, 중앙 −30%p) 같은 업종의
                               # 충격이 대분류에 묻혀 사라짐. 업종 특성이 핵심이라 작은 표본을 감수 (결정표 12장)
SHOCK_BIG_DROP, SHOCK_BIG_Z = -0.01, -1.0   # '큰 충격' 기준: 영업이익률 변화 −1%p 이하이고 그 업종 평소 대비 z ≤ −1 (사건카탈로그와 같음)
GSTAR_LIMIT = 0.10             # g*가 10%를 넘으면 숫자 대신 표시 (문서 2-5)
RANGE_UPPER_SHOW_MAX = GSTAR_LIMIT   # 협상 구간 상한이 10%를 넘으면 숫자 대신 '10% 초과' (g*와 같은 약속, 11-22)
RANGE_HOLD_TEXT = '업계 적자로 인한 상한 산출 보류'   # 비교군 이익÷급여 중앙값이 0 이하일 때 (11-22 팀 결정 문구)
VOL_MIN_CHANGES = 5            # 평소 변동: 연속한 두 해의 변화값 최소 개수 (문서 2-4)
VOL_OPM_ABS_MAX = 1.0          # 영업이익률 평소 변동: |영업이익률| < 100%인 해만
VOL_WAGE_ABS_MAX = 0.5         # 급여 증가율 변동성: |ln 변화| < 0.5인 해만


WS_RANGE = (0.8, 2.0)          # 급여 확인: W ÷ S 정상 범위 (문서 2-7)
AVG_RANGE = (0.8, 1.25)        # 급여 확인: 공시 평균급여 ÷ (S/N) 정상 범위 (문서 2-7)

SIZE_BANDS = [0, 299, 999, 1e9]                # 직원 구간 (WPS 연결, 문서 3장)
SIZE_LABELS = ['~299', '300~999', '1000~']
WPS_MIN_SAMPLE = 10            # WPS 칸 공개 하한 (문서 3장)
WPS_WAVES = [2015, 2017, 2019, 2021, 2023]     # WPS 조사 연도

# =====================================================================
# [이름표]
# =====================================================================
RENAME = {'기업고유코드': 'id', '사업연도': 'yr', '기업명': 'name', '직원수': 'N', '급여총액(원)': 'S',
          '영업이익(원)': 'OP', '매출액(원)': 'REV', '자산총계(원)': 'AST', '이자비용(원)': 'INT',
          '감가상각비(원)': 'DEP', '세금과공과(원)': 'TAX', '대손상각비(원)': 'BAD', '인건비총액W(원)': 'W',
          '업종코드_중분류': 'ind2', '상장시장': 'mkt'}

SECTION_RANGES = [(1, 3, 'A'), (5, 8, 'B'), (10, 34, 'C'), (35, 35, 'D'), (36, 39, 'E'), (41, 42, 'F'),
                  (45, 47, 'G'), (49, 52, 'H'), (55, 56, 'I'), (58, 63, 'J'), (64, 66, 'K'), (68, 68, 'L'),
                  (70, 73, 'M'), (74, 76, 'N'), (84, 84, 'O'), (85, 85, 'P'), (86, 87, 'Q'), (90, 91, 'R'),
                  (94, 96, 'S')]
SECTION_NAME = {'A': '농림어업', 'B': '광업', 'C': '제조업', 'D': '전기·가스', 'E': '수도·하수·폐기물', 'F': '건설업',
                'G': '도소매업', 'H': '운수·창고', 'I': '숙박·음식', 'J': '정보통신', 'K': '금융·보험', 'L': '부동산',
                'M': '전문·과학·기술', 'N': '사업시설·사업지원', 'O': '공공행정', 'P': '교육', 'Q': '보건·복지',
                'R': '예술·스포츠·여가', 'S': '협회·수리·개인서비스'}
IND2_NAME = {1: '농업', 2: '임업', 3: '어업', 5: '석탄·원유·가스 광업', 6: '금속 광업', 7: '비금속광물 광업', 8: '광업 지원',
             10: '식료품', 11: '음료', 12: '담배', 13: '섬유제품', 14: '의복·모피', 15: '가죽·가방·신발', 16: '목재·나무제품',
             17: '펄프·종이', 18: '인쇄·기록매체', 19: '코크스·석유정제', 20: '화학물질·화학제품', 21: '의료용 물질·의약품',
             22: '고무·플라스틱', 23: '비금속 광물제품', 24: '1차 금속', 25: '금속가공제품',
             26: '전자부품·컴퓨터·통신장비(반도체 등)', 27: '의료·정밀·광학기기', 28: '전기장비(2차전지 등)',
             29: '기타 기계·장비', 30: '자동차·트레일러', 31: '기타 운송장비(조선·항공 등)', 32: '가구', 33: '기타 제품',
             34: '산업용 기계 수리', 35: '전기·가스·증기', 36: '수도', 37: '하수·폐수 처리', 38: '폐기물 처리·재활용',
             39: '환경정화', 41: '종합 건설', 42: '전문직별 공사', 45: '자동차 판매', 46: '도매', 47: '소매', 49: '육상 운송',
             50: '수상 운송', 51: '항공 운송', 52: '창고·운송 서비스', 55: '숙박', 56: '음식점',
             58: '출판(게임·소프트웨어 포함)', 59: '영상·오디오 제작', 60: '방송', 61: '통신', 62: '컴퓨터 프로그래밍·SI',
             63: '정보서비스(포털 등)', 68: '부동산', 70: '연구개발', 71: '전문서비스(법무·회계·광고 등)',
             72: '건축기술·엔지니어링', 73: '기타 전문(디자인·사진 등)', 74: '사업시설 관리', 75: '사업지원', 76: '임대', 85: '교육',
             86: '보건', 87: '사회복지', 90: '창작·예술', 91: '스포츠·오락', 94: '협회·단체', 95: '개인용품 수리',
             96: '기타 개인서비스'}


def ksic_section(ind2):
    """중분류(정수) → 대분류 글자. 범위 밖이면 'Z'."""
    i = int(ind2)
    for low, high, sec in SECTION_RANGES:
        if low <= i <= high:
            return sec
    return 'Z'


def eok(x):
    """금액 표시: 1억 이상은 억 원, 미만은 만 원."""
    return f'{x / 1e8:,.0f}억 원' if abs(x) >= 1e8 else f'{x / 1e4:,.0f}만 원'


# =====================================================================
# 1. 자료 읽기
# =====================================================================
def load_panel(path):
    """DART 패널 CSV를 읽어 짧은 열 이름(id, yr, S, N, OP …)으로 바꾼다. 원본은 읽기만 한다."""
    df = pd.read_csv(path, encoding='utf-8-sig',
                     dtype={'기업고유코드': str, '종목코드': str, '업종코드': str, '업종코드_중분류': str})
    df = df.rename(columns=RENAME)
    df['ind2'] = pd.to_numeric(df['ind2'], errors='coerce').astype(int)
    df['sec'] = df['ind2'].map(ksic_section)
    return df


def load_cfo(folder, years=range(2015, 2026)):
    """영업활동현금흐름: DART 정형재무(별도) 파일 `{folder}\\{연도}\\10_정형재무_OFS_당기.csv`. 없는 연도는 건너뜀."""
    out = []
    for y in years:
        p = os.path.join(folder, str(y), '10_정형재무_OFS_당기.csv')
        if not os.path.exists(p):
            continue
        f = pd.read_csv(p, encoding='utf-8-sig', dtype=str, usecols=['기업고유코드', '계정명', '금액원'])
        f = f[f['계정명'].str.replace(r'\s', '', regex=True).isin(['영업활동현금흐름', '영업활동으로인한현금흐름'])]
        f['CFO'] = pd.to_numeric(f['금액원'].str.replace(',', ''), errors='coerce')
        out.append(f.groupby('기업고유코드').CFO.first().reset_index().rename(columns={'기업고유코드': 'id'}).assign(yr=y))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=['id', 'yr', 'CFO'])


WPS_COLUMNS = ['year', 'ind10', 'ind9', 'aq1001', 'aq2001', 'aq2003', 'fpq1001', 'fpq1011', 'epq1011',
               'cq2104', 'cq3001', 'cq3002', 'cq3003', 'cq3007', 'mq1001', 'epq4008', 'epq8041']


def load_wps(path_or_pattern):
    """WPS 원자료에서 필요한 열만 읽는다. 원자료는 이용 조건 때문에 공유하지 않는다(문서 3장).
    파일 이름이 자모 분리형(NFD)일 수 있어 패턴으로도 찾는다."""
    path = path_or_pattern
    if not os.path.exists(path):
        hits = [p for p in glob.glob(os.path.join(os.path.dirname(path), '*'))
                if unicodedata.normalize('NFC', os.path.basename(p)) == unicodedata.normalize('NFC', os.path.basename(path))]
        if not hits:
            raise FileNotFoundError(path)
        path = hits[0]
    hdr = pd.read_csv(path, nrows=0).columns
    w = pd.read_csv(path, usecols=[c for c in WPS_COLUMNS if c in hdr], low_memory=False)
    return w[w.year >= 2015].copy()


# =====================================================================
# 2. 분석 표본 (결정표 1장)
# =====================================================================
def mark_sample(panel, upto=None):
    """단위 이상·기본 조건·재무 조건·비금융을 표시한다.
    upto: None이면 전체 기간 중앙값으로 단위 이상을 판정(진단용), 연도를 주면 그해까지만 씀(모델용, 미래 정보 차단)."""
    d = (panel if upto is None else panel[panel.yr <= upto]).copy()
    if 'sec' not in d:                            # load_panel을 거치지 않고 직접 읽은 패널(노트북)일 때
        d['sec'] = d['ind2'].map(ksic_section)
    for v, limit in UNIT_LIMIT.items():
        g = d.groupby('id')[v]
        ratio = d[v] / g.transform('median')
        d['x_' + v] = ((ratio > limit) | (ratio < 1 / limit)) & (g.transform('count') >= UNIT_MIN_OBS) & (d[v] > 0)
    d['x_OP'] = (d.OP.abs() > OP_TO_ASSET_LIMIT * d.AST) & d.AST.notna()
    d['base'] = (d.N.notna() & d.S.notna() & (d.N >= MIN_EMPLOYEES) & (d[FLAGS].sum(axis=1) == 0)
                 & ~d.x_N & ~d.x_S)
    d['fin_ok'] = d.OP.notna() & ~d.x_OP & ~d.x_AST & ~d.x_REV
    d['core'] = d.base & d.fin_ok & ~d.ind2.between(*FINANCE_IND2)
    d['w'] = d.S / d.N
    return d


def clean_depreciation(d):
    """감가상각비 이상값은 값만 비운다(행 유지): 음수, 패널 감가이상 플래그, 같은 기업 양수 중앙값 대비 5배 초과·1/5 미만."""
    d = d.copy()
    positive = d.DEP.where(d.DEP > 0)
    med = positive.groupby(d['id']).transform('median')
    cnt = positive.groupby(d['id']).transform('count')
    ratio = d.DEP / med
    bad = (d.DEP < 0) | d['플래그_감가이상'].eq(1) | (((ratio > DEP_LIMIT) | (ratio < 1 / DEP_LIMIT)) & (cnt >= DEP_MIN_OBS))
    d['DEPf'] = d.DEP.where(~bad)
    d['감가_비움'] = bad & d.DEP.notna()
    return d


def _lag(c, col):
    """같은 기업의 바로 전 해 값 (연도가 이어질 때만)."""
    g = c.groupby('id')
    return g[col].shift(1).where(g.yr.shift(1) == c.yr - 1)


def weak_year(op, interest):
    """연도별 한계 신호: 이자비용 > 0이면 이자보상비율(OP ÷ 이자) < 1, 이자비용이 없거나 0 이하면 영업적자."""
    return np.where(interest > 0, (op / interest) < 1, op < 0)


def build_core(panel, cfo=None, emp=None, upto=None, clean_dep=True):
    """분석 표본(core) 행에 계산 재료를 붙인다.
    cfo: id·yr·CFO (load_cfo), emp: id·yr·avg_disc(공시 1인 평균급여). 둘 다 없으면 해당 표시를 하지 않는다.
    clean_dep=False: 감가상각비 이상값을 이미 비운 자료(노트북 2-1)일 때. 이때는 DEP를 그대로 DEPf로 쓴다."""
    d = mark_sample(panel, upto)
    if clean_dep:
        d = clean_depreciation(d)
    else:
        d['DEPf'] = d.DEP
    core = d[d.core].copy()
    core['CFO'] = np.nan
    core['avg_disc'] = np.nan
    if cfo is not None and len(cfo):
        core = core.drop(columns='CFO').merge(cfo.astype({'id': core['id'].dtype}), on=['id', 'yr'], how='left')
    if emp is not None and len(emp):
        e = emp[['id', 'yr', 'avg_disc']].astype({'id': core['id'].dtype})
        core = core.drop(columns='avg_disc').merge(e, on=['id', 'yr'], how='left')
    core['CFO'] = pd.to_numeric(core['CFO'], errors='coerce')
    core['avg_disc'] = pd.to_numeric(core['avg_disc'], errors='coerce')
    core = core.sort_values(['id', 'yr']).reset_index(drop=True)
    core['opm'] = (core.OP / core.REV).where(core.REV > 0)
    core['dopm'] = core.opm - _lag(core, 'opm')
    core['lw'] = np.log(core.w)
    core['dlw'] = core.lw - _lag(core, 'lw')
    core['low'] = weak_year(core.OP, core.INT)
    core['ws'] = core.W / core.S
    core['avgchk'] = core.avg_disc / core.w
    return core


# =====================================================================
# 3. 구간 자료
# =====================================================================
def window(core, start, end):
    """구간 모든 해가 분석 표본인 기업만, 3년 합산 + 마지막 해 값."""
    n = end - start + 1
    d = core[core.yr.between(start, end)]
    g = d.groupby('id')
    o = pd.DataFrame({
        'k': g.size(), 'name': g.name.last(), 'mkt': g.mkt.last(), 'ind2': g.ind2.last(), 'sec': g.sec.last(),
        'S': g.S.sum(), 'N': g.N.sum(), 'OP': g.OP.sum(),
        'REV': g.REV.sum(min_count=n), 'AST': g.AST.sum(min_count=n), 'CFO': g.CFO.sum(min_count=n),
        'lossyrs': g.OP.apply(lambda s: int((s < 0).sum())), '한계': g.low.all(), 'low_n': g.low.sum(),
        'ws_bad': g.ws.apply(lambda s: bool(((s < WS_RANGE[0]) | (s > WS_RANGE[1])).any())),
        'ws_any': g.ws.apply(lambda s: bool(s.notna().any())),
        'avg_bad': g.avgchk.apply(lambda s: bool(((s < AVG_RANGE[0]) | (s > AVG_RANGE[1])).any())),
        'avg_any': g.avgchk.apply(lambda s: bool(s.notna().any())),
    })
    o = o[o.k == n].copy()
    last = d[d.yr == end].set_index('id')
    for c in ['S', 'OP', 'REV', 'DEPf', 'TAX', 'BAD', 'N']:
        o[c + '_T'] = last[c].reindex(o.index)
    o['Nbar'] = o.N / n
    o['sz'] = pd.cut(o.Nbar, SIZE_BANDS, labels=SIZE_LABELS).astype(str)
    o['w'] = o.S / o.N
    o['opm'] = (o.OP / o.REV).where(o.REV > 0)
    o['sr'] = (o.S / o.REV).where(o.REV > 0)
    o['LS'] = (o.S / (o.S + o.OP)).where((o.S + o.OP) > 0)
    o['ok'] = (o.REV > 0) & (o.AST > 0)
    o['lrev'] = np.log(o.REV.where(o.ok))
    o['lk'] = np.log((o.AST / o.N).where(o.ok))
    o.attrs.update(start=start, end=end, years=n)
    return o


# =====================================================================
# 4. 기능 1 — 임금 위치 (결정표 2·3장)
# =====================================================================
def select_peers(dist_row, ind2, own_ind2, exclude=None, k=PEER_COUNT):
    """비교군 고르기: ① 같은 중분류에서 거리 가까운 순 → ② 20곳이 안 되면 같은 대분류의 다른 중분류에서 가까운 순으로 채움.
    dist_row: 후보(같은 대분류 기업)까지의 거리, ind2: 후보의 중분류, own_ind2: 내 중분류, exclude: 후보 중 나 자신의 위치."""
    idx = np.arange(len(ind2))
    keep = idx != exclude if exclude is not None else np.ones(len(ind2), bool)
    same = idx[(ind2 == own_ind2) & keep]
    other = idx[(ind2 != own_ind2) & keep]
    same = same[np.argsort(dist_row[same], kind='stable')]
    other = other[np.argsort(dist_row[other], kind='stable')]
    return np.concatenate([same, other])[:k]


def wage_position(o, k=PEER_COUNT):
    """비교군 20곳 → 기준 급여(중앙값)·임금 차이·순위 P·판정·참고 구간."""
    o = o.copy()
    for c in ['ref', 'ref25', 'ref75', 'P', 'rr', 'sr_ref', 'n_same']:
        o[c] = np.nan
    peer_rows = []
    for _, gg in o[o.ok].groupby('sec'):
        if len(gg) < k + 1:                       # 대분류가 21곳 미만 → 비교 불가
            continue
        X = gg[['lrev', 'lk']].values
        sd = X.std(0)
        sd[sd == 0] = 1
        X = (X - X.mean(0)) / sd                  # 같은 대분류 안에서 표준화
        dist = ((X[:, None, :] - X[None, :, :]) ** 2).sum(-1)
        iv = gg.ind2.to_numpy()
        idx = np.array([select_peers(dist[i], iv, iv[i], exclude=i, k=k) for i in range(len(gg))])
        wv, rev, ids = gg.w.values, gg.REV.values, gg.index.to_numpy()
        nb = wv[idx]
        o.loc[ids, 'ref'] = np.median(nb, 1)
        o.loc[ids, 'ref25'] = np.percentile(nb, REF_BAND[0], axis=1)
        o.loc[ids, 'ref75'] = np.percentile(nb, REF_BAND[1], axis=1)
        o.loc[ids, 'P'] = ((nb < wv[:, None]).sum(1) + 0.5 * (nb == wv[:, None]).sum(1)) / k
        o.loc[ids, 'rr'] = np.median(rev[idx], 1) / rev
        o.loc[ids, 'sr_ref'] = np.nanmedian(gg.sr.values[idx], 1)
        o.loc[ids, 'n_same'] = (iv[idx] == iv[:, None]).sum(1)
        for i, firm in enumerate(ids):
            for rank, j in enumerate(idx[i], 1):
                peer_rows.append((firm, rank, ids[j], iv[j] == iv[i], dist[i, j]))
    o['임금 차이(%)'] = (o.w / o.ref - 1) * 100
    o['임금 위치'] = np.where(o.P.isna(), '비교 불가',
                          np.where(o.P >= HIGH_P, '임금 높음', np.where(o.P <= LOW_P, '임금 낮음', '임금 보통')))
    o['비교군 주의'] = np.where(o.P.isna(),
                           np.where(o.ok, '대분류 기업 수 부족(21곳 미만)', '매출·자산 없음'),
                           np.where((o.rr < 1 / SIZE_GAP) | (o.rr > SIZE_GAP), '비교 기업의 매출 규모가 크게 다름', ''))
    peers = pd.DataFrame(peer_rows, columns=['id', '순번', 'peer_id', '같은 중분류', '거리'])
    return o, peers


# =====================================================================
# 5. 기능 1 — 지급 여력 (결정표 4장)
# =====================================================================
def pay_capacity(o, years=YEARS_IN_WINDOW):
    """영업이익률을 업종 기준(중분류 → 대분류 → 전체 중앙값)과 비교. 제약 → 판정 불가 → 있음 → 보통 순서."""
    o = o.copy()
    n = years
    n2 = o.groupby('ind2').opm.transform('count')
    n1 = o.groupby('sec').opm.transform('count')
    o['opm_ind'] = np.where(n2 >= INDUSTRY_MIN_FIRMS, o.groupby('ind2').opm.transform('median'),
                            np.where(n1 >= INDUSTRY_MIN_FIRMS, o.groupby('sec').opm.transform('median'), o.opm.median()))
    o['업종기준단위'] = np.where(n2 >= INDUSTRY_MIN_FIRMS, '중분류', np.where(n1 >= INDUSTRY_MIN_FIRMS, '대분류', '전체'))
    loss = o.OP < 0
    zombie = o['한계'].astype(bool)
    o['지급 여력'] = np.where(loss | zombie, '여력 제약',
                          np.where(o.opm.isna(), '판정 불가', np.where(o.opm >= o.opm_ind, '여력 있음', '여력 보통')))
    o['여력 사유'] = np.where(loss & zombie, f'{n}년 합산 영업적자, 이자보상비율 {n}년 연속 1 미만',
                          np.where(loss, f'{n}년 합산 영업적자', np.where(zombie, f'이자보상비율 {n}년 연속 1 미만', '')))
    o['현금흐름 표시'] = np.where((o.CFO < 0) & o.CFO.notna(), '장부상 이익과 실제 현금이 다름(영업현금흐름 합 적자)', '')
    return o


# =====================================================================
# 6. 기능 2~4 — 비용 (결정표 5장)
# =====================================================================
def volatility(core, end):
    """평소 변동 (구간 끝까지의 자료): 영업이익률 변화의 표준편차 opm_sd, 1인당 급여 ln 변화의 표준편차 w_sd."""
    hist = core[core.yr <= end]
    v = hist[hist.opm.abs() < VOL_OPM_ABS_MAX].groupby('id').dopm.agg(['std', 'count'])
    opm_sd = v[v['count'] >= VOL_MIN_CHANGES]['std'].rename('opm_sd')
    v = hist[hist.dlw.abs() < VOL_WAGE_ABS_MAX].groupby('id').dlw.agg(['std', 'count'])
    w_sd = v[v['count'] >= VOL_MIN_CHANGES]['std'].rename('w_sd')
    return pd.concat([opm_sd, w_sd], axis=1)


def cost(o, rate=PAY_RATE, c=OVERHEAD_C):
    """급여의 rate만큼 더 줄 때: 회사 추가 비용 ΔW, 영업이익률 하락, 비용÷영업이익, g*, 평소 변동 대비. 모두 마지막 1년 값."""
    o = o.copy()
    o['D상태'] = np.where(o.DEPf_T.isna(), '간이', np.where(o.TAX_T.notna() & o.BAD_T.notna(), '정식', '보완'))
    o['D_T'] = (o.DEPf_T + o.TAX_T.fillna(0) + o.BAD_T.fillna(0)).where(o.DEPf_T.notna())
    o['A_T'] = o.S_T + o.OP_T + o.D_T.fillna(0)
    o['dW'] = rate * o.S_T * (1 + c)
    o['하락'] = (o.dW / o.REV_T * 100).where(o.REV_T > 0)
    o['비용÷영업이익'] = (o.dW / o.OP_T * 100).where(o.OP_T > 0)
    g = o.dW / o.A_T
    o['g*원값'] = (g * 100).where(o.A_T > 0)
    o['g*'] = (g * 100).where((o.A_T > 0) & (g <= GSTAR_LIMIT))
    o['g*표시'] = np.where(o.A_T <= 0, '계산 불가(부가가치 0 이하)',
                         np.where(g > GSTAR_LIMIT, '10% 초과(부가가치에 비해 비용이 큼)', ''))
    if 'opm_sd' in o:
        o['평소변동대비'] = o['하락'] / (o.opm_sd * 100)
    o['인상 계산'] = np.where(o['지급 여력'] == '여력 제약', '인상 시나리오 대신 지급 여력 점검 경고', '계산')
    o.attrs.update(pay_rate=rate, overhead=c)
    return o


# =====================================================================
# 7. 기능 5 — 이익연동 전환 시뮬레이션 (결정표 6장)
# =====================================================================
def profit_share_rate(o, rate=PAY_RATE):
    """이익연동 전환의 시작값: 급여의 rate와 같은 금액이 되는 영업이익 비율 = rate × ΣS ÷ ΣOP (진단과 같은 3년 합산).
    3년 합산 영업이익이 0 이하면 계산하지 않는다. (과거 연도에 비율을 적용해 보는 계산은 하지 않음, 11-21 결정)"""
    a = (rate * o.S / o.OP).where(o.OP > 0)
    return pd.DataFrame({'전환_같은 금액이 되는 영업이익 비율(%)': a * 100,
                         '전환_표시': np.where(o.OP > 0, '', '3년 합산 영업적자라 계산하지 않음')}, index=o.index)


# =====================================================================
# 7-b. 업황 충격 시나리오 (결정표 12장)
# =====================================================================
def shock_table(core, end):
    """업종×연도 충격표 (기능 4 업계 불황 대비 점검의 재료). 구간 끝까지의 자료만.
    기업별 '영업이익률 변화(전년 대비)'와 '매출 변화(ln)'를 업종·연도로 모아 중앙값과 하위 25%를 구한다.
    앞뒤 두 해 모두 |영업이익률| < 100%인 변화만 쓴다(적자 −100% 수준에서의 회복 같은 극단값 제외).
    반환: {'중분류': (ind2, yr) 표, '대분류': (sec, yr) 표, '전체': yr 표}. 열 = 기업수, 이익률변화, 이익률변화_하위25,
          매출변화, 매출변화_하위25 (모두 소수, 매출은 증가율), 중분류 표에는 평소 대비 z와 큰 충격 여부도"""
    c = core[core.yr <= end].copy()
    c['lrev'] = np.log(c.REV.where(c.REV > 0))
    c['dlrev'] = c.lrev - _lag(c, 'lrev')
    h = c[c.dopm.notna() & (c.opm.abs() < VOL_OPM_ABS_MAX) & ((c.opm - c.dopm).abs() < VOL_OPM_ABS_MAX)]

    def agg(keys):
        t = h.groupby(keys).agg(기업수=('dopm', 'size'), 이익률변화=('dopm', 'median'),
                                이익률변화_하위25=('dopm', lambda x: x.quantile(.25)),
                                매출변화=('dlrev', 'median'), 매출변화_하위25=('dlrev', lambda x: x.quantile(.25)))
        for col in ['매출변화', '매출변화_하위25']:
            t[col] = np.expm1(t[col])
        return t

    t2 = agg(['ind2', 'yr'])
    ok = t2[t2.기업수 >= SHOCK_MIN_FIRMS]
    mu = ok.groupby(level=0).이익률변화.mean()
    sd = ok.groupby(level=0).이익률변화.std()
    lv = t2.index.get_level_values(0)
    t2['평소대비z'] = ((t2.이익률변화 - mu.reindex(lv).to_numpy()) / sd.reindex(lv).to_numpy()).where(t2.기업수 >= SHOCK_MIN_FIRMS)
    t2['큰충격'] = (t2.이익률변화 <= SHOCK_BIG_DROP) & (t2.평소대비z <= SHOCK_BIG_Z)
    return {'중분류': t2, '대분류': agg(['sec', 'yr']), '전체': agg(['yr'])}


def firm_shock(tables, ind2, sec, yr, severity='중앙'):
    """한 기업에 적용할 그해의 업종 충격. 같은 중분류(3곳 이상) → 같은 대분류(3곳 이상) → 전체.
    severity: '중앙'(그 업종의 보통 회사) 또는 '하위25'(많이 맞은 회사). 반환: dict(이익률변화, 매출변화, 단위, 기업수)"""
    sfx = '_하위25' if severity == '하위25' else ''
    for unit, t, key in [('중분류', tables['중분류'], (ind2, yr)), ('대분류', tables['대분류'], (sec, yr)), ('전체', tables['전체'], yr)]:
        if key in t.index and (unit == '전체' or t.loc[key, '기업수'] >= SHOCK_MIN_FIRMS):
            r = t.loc[key]
            return {'이익률변화': r['이익률변화' + sfx], '매출변화': r['매출변화' + sfx], '단위': unit, '기업수': int(r['기업수'])}
    return {'이익률변화': np.nan, '매출변화': np.nan, '단위': '', '기업수': 0}


def load_catalog(path):
    """사건카탈로그.csv (업황 사건: 업종·연도·확인 수준·출처·기능 4 선택지)."""
    cat = pd.read_csv(path, encoding='utf-8-sig')
    cat['중분류코드'] = cat['중분류코드'].astype(str)
    return cat


# =====================================================================
# 7-c. 인사팀 기능 — 기능 2 인상안 협상 구간(하한·상한 + 인상 결정 + 노조안 비교) (결정표 12장)
# =====================================================================
def peer_growth(core, o, peers, end, years=PEER_GROWTH_YEARS):
    """기업마다 비교군 20곳의 최근 연 1인당 급여 증가율 중앙값 (ln 변화 평균 → 증가율)."""
    h = core[(core.yr > end - years) & (core.yr <= end) & (core.dlw.abs() < VOL_WAGE_ABS_MAX)]
    g = h.groupby('id').dlw.agg(['mean', 'count'])
    g = np.expm1(g.loc[g['count'] >= 2, 'mean'])
    pg = peers.assign(g=peers.peer_id.map(g)).groupby('id').g.median()
    return pg.reindex(o.index)


def _range_core(lower, ops, peer_ops, op_T, s_T, c_base=OVERHEAD_C_BASE):
    """인상안 협상 구간의 하한·상한 (평상시 기준, 기본급 인상률). 결정표 14장.
    하한 = 비교군 인상률 (업계만큼 올리기, 노측 근거)
    상한 = 하한 × (우리 이익÷급여) ÷ (비교군 이익÷급여 중앙값) (업계만큼만 부담하기, 사측 근거)
         = 인상 비용 ÷ 영업이익이 비교군과 같아지는 인상률 (기존 '비용÷영업이익'을 거꾸로 푼 것, c′는 약분)
         단, 마지막 해 영업이익을 넘는 인상(적자 전환)은 넘지 않게 제한
    업황은 넣지 않는다 (업계 불황 대비 점검 = 기능 4에서만, 11-21 결정)"""
    out = {'하한': lower, '상한': np.nan, '상한 원값': np.nan, '상한 표시': '', '상한 상태': '', '구간 해석': ''}
    if pd.isna(lower):
        out.update({'상한 상태': '비교군 인상률 없음', '상한 표시': '비교군 인상률 없음'})
        return out
    if pd.isna(peer_ops) or peer_ops <= 0:
        out.update({'상한 상태': RANGE_HOLD_TEXT, '상한 표시': RANGE_HOLD_TEXT,
                    '구간 해석': '하한(업계 인상률)만 제시. 고정 인상보다 이익연동 전환을 함께 검토'})
        return out
    if pd.isna(ops) or ops <= 0:
        raw, state = 0.0, '3년 합산 영업적자'
    else:
        raw, state = lower * ops / peer_ops, '계산'
    cap = op_T / (s_T * (1 + c_base)) if (pd.notna(op_T) and op_T > 0 and s_T > 0) else 0.0
    upper = min(raw, cap)
    if state == '계산' and cap < raw:
        state = '적자 전환 직전에서 제한'
    out.update({'상한': upper, '상한 원값': raw, '상한 상태': state,
                '상한 표시': f'{RANGE_UPPER_SHOW_MAX:.0%} 초과' if upper > RANGE_UPPER_SHOW_MAX else f'{upper:.1%}',
                '구간 해석': ('업계 수준 이상도 업계만큼의 부담으로 감당 가능' if upper >= lower
                          else '업계만큼 주면 우리 부담이 업계보다 큼. 이익연동 전환 검토')})
    return out


def negotiation_range(ctx, firm, peer_raise=None):
    """기능 2 「인상안 협상 구간」의 첫 화면: 하한(업계 인상률)~상한(업계와 같은 부담 수준).
    peer_raise: 업계 인상률을 직접 넣으면(협회 조사 등) 하한과 상한이 같이 바뀐다. None이면 비교군 최근 3년 중앙값."""
    f = ctx.firms.loc[firm]
    lower = f['비교군 인상률'] if peer_raise is None else peer_raise
    return pd.Series(_range_core(lower, f['OP_avg'] / f['S_avg'] if f['S_avg'] > 0 else np.nan,
                                 f.get('비교군 이익÷급여', np.nan), f['OP_T'], f['S_T']))


def range_position(rate, rng):
    """안(기본급 인상률)이 협상 구간의 어디에 있는지.
    상한이 10%를 넘어 '10% 초과'로 표시되는 회사는, 하한 이상인 안을 모두 '구간 안'으로 본다(표시 약속과 맞춤)."""
    lo, up = rng['하한'], rng['상한']
    if pd.isna(lo):
        return ''
    if pd.isna(up):                                              # 업계 적자로 인한 상한 산출 보류
        return '하한 미달' if rate < lo else '하한 이상 (상한 산출 보류)'
    if up >= lo:
        if rate < lo:
            return '하한 미달'
        if up > RANGE_UPPER_SHOW_MAX:
            return f'구간 안 (상한 {RANGE_UPPER_SHOW_MAX:.0%} 초과)'
        return '구간 안' if rate <= up else '상한 초과'
    # 상한 < 하한: 업계만큼 주면 업계보다 부담이 큰 회사
    return '상한 이하' if rate <= up else ('상한 초과·하한 미달' if rate < lo else '하한 이상·상한 초과')


def sim_context(res, core, catalog=None):
    """시뮬레이터에 필요한 기업별 재료를 한 번에 모은다 (MVP는 이 표만 읽으면 됨).
    catalog: load_catalog() 결과(없으면 업황 선택지에 사건 이름 없이 공통 사건·최악의 해·직접 입력만)
    반환: SimpleNamespace(firms=기업별 표, peer_w={id: 비교군 20곳의 마지막 해 1인당 급여 배열}, shocks=업종×연도 충격표,
          catalog, end)"""
    from types import SimpleNamespace
    end = res.attrs['end']
    peers = res.attrs['peers']
    last = core[core.yr == end].set_index('id')
    f = pd.DataFrame(index=res.index)
    f['name'], f['ind2'], f['sec'] = res['name'], res['ind2'], res['sec']
    for c in ['S_T', 'N_T', 'OP_T', 'REV_T', 'D_T', 'opm_sd', 'opm', 'sr', 'sr_ref', 'w', '지급 여력']:
        f[c] = res[c]
    f['w_T'] = (last.S / last.N).reindex(f.index)
    f['비교군 인상률'] = peer_growth(core, res, peers, end)
    f['α*'] = res['전환_같은 금액이 되는 영업이익 비율(%)'] / 100
    ops = (res['OP'] / res['S']).where(res['S'] > 0)                        # 3년 합산 영업이익 ÷ 급여총액
    f['이익÷급여'] = ops
    f['비교군 이익÷급여'] = peers.assign(r=peers.peer_id.map(ops)).groupby('id').r.median().reindex(f.index)
    yrs = res.attrs.get('years', YEARS_IN_WINDOW)
    for a, b in [('S', 'S_avg'), ('OP', 'OP_avg'), ('REV', 'REV_avg'), ('N', 'N_avg')]:   # 이익연동 전환은 3년 연평균 기준
        f[b] = res[a] / yrs
    shocks = shock_table(core, end)
    big = shocks['중분류']['큰충격']
    f['기준연도 업종 충격'] = [bool(big.get((i, end), False)) for i in f.ind2]   # 기준 연도가 이미 그 업종의 큰 충격 해
    wT = f['w_T']
    peer_w = {i: wT.reindex(g.peer_id).to_numpy() for i, g in peers.groupby('id')}
    rng = pd.DataFrame([_range_core(r['비교군 인상률'], r['이익÷급여'], r['비교군 이익÷급여'], r['OP_T'], r['S_T'])
                        for _, r in f.iterrows()], index=f.index)
    f = f.join(rng[['하한', '상한', '상한 원값', '상한 표시', '상한 상태', '구간 해석']])
    return SimpleNamespace(firms=f, peer_w=peer_w, shocks=shocks, catalog=catalog, end=end)


def _rank(w, arr):
    arr = arr[~np.isnan(arr)]
    return ((arr < w).sum() + 0.5 * (arr == w).sum()) / len(arr) if len(arr) else np.nan


def pay_plan(ctx, firm, base_raise=0.0, bonus=0.0, headcount=0.0, sales_growth=0.0, peer_raise=None,
             c=OVERHEAD_C, c_base=OVERHEAD_C_BASE):
    """인상 결정: 기본급 인상률·일시 성과급(+ 선택: 인원 증감·매출 증가율)을 넣으면 비용, 내년 숫자, 업종 내 위치를 한 번에.
    (11-21까지의 raise_sim·budget_sim을 합친 것. 인원·매출을 0으로 두면 '올해 숫자에 이 인상안을 넣으면'이 된다)
    - 내년 급여(성과급 제외) S1 = S_T × (1 + 인원) × (1 + 기본급), 성과급 = bonus × S1 (바뀐 급여 기준)
    - 회사 부담 증가 = (S1 − S_T) × (1 + c′) + 성과급 × (1 + c). 3년 누적 = 인원·기본급분 × 3 + 성과급분 (성과급 1회)
    - 지급 전 영업이익(내년) = 영업이익_T + 늘어난 매출 × 지금 영업이익률 (단순 가정). 평상시 기준이고,
      불황이 오면 어떻게 되는지는 기능 4 업계 불황 대비 점검(stress_test)에서만 본다 (11-21 결정)
    - 위치: 마지막 해 1인당 급여 × (1 + 기본급)(1 + 성과급) vs 비교군 × (1 + 비교군 인상률).
      peer_raise=None이면 비교군 최근 3년 증가율 중앙값"""
    f = ctx.firms.loc[firm]
    S0, N0, REV = f.S_T, f.N_T, f.REV_T
    OP = f.OP_T
    S1 = S0 * (1 + headcount) * (1 + base_raise)
    B1 = bonus * S1
    d_head = S0 * headcount * (1 + c_base)
    d_raise = S0 * (1 + headcount) * base_raise * (1 + c_base)
    d_bonus = B1 * (1 + c)
    dW = d_head + d_raise + d_bonus
    REV1 = REV * (1 + sales_growth)
    OP_pre = OP + (REV1 - REV) * (OP / REV if REV > 0 else 0)
    N1 = N0 * (1 + headcount)
    A = S0 + OP + (f.D_T if pd.notna(f.D_T) else 0)
    drop = dW / REV1 * 100 if REV1 > 0 else np.nan
    g_peer = f['비교군 인상률'] if peer_raise is None else peer_raise
    pw = ctx.peer_w.get(firm, np.array([]))
    w_now, w_next = f.w_T, f.w_T * (1 + base_raise) * (1 + bonus)
    pw_next = pw * (1 + (g_peer if pd.notna(g_peer) else 0))
    med_now = np.nanmedian(pw) if len(pw) else np.nan
    med_next = np.nanmedian(pw_next) if len(pw) else np.nan
    return pd.Series({
        '기본급 인상률': base_raise, '일시 성과급(급여 대비)': bonus, '인원 증감': headcount, '매출 증가율': sales_growth,
        # 비용
        '회사 부담 증가(1년)': dW, '그중 인원분': d_head, '그중 기본급 인상분': d_raise, '그중 성과급분': d_bonus,
        '3년 누적 부담(인원·기본급 유지 + 성과급 1회)': 3 * (d_head + d_raise) + d_bonus,
        '지급 전 영업이익(내년)': OP_pre, '지급 후 영업이익(내년)': OP_pre - dW,
        '영업이익률 하락(%p)': drop,
        '비용÷영업이익(%)': dW / OP_pre * 100 if OP_pre > 0 else np.nan,
        '지급 때문에 적자 전환': bool(OP_pre >= 0 and OP_pre - dW < 0),
        'g*(%)': dW / A * 100 if A > 0 else np.nan,
        '평소 변동 대비': drop / (f.opm_sd * 100) if pd.notna(f.opm_sd) and f.opm_sd > 0 else np.nan,
        # 내년 숫자
        '올해 급여총액': S0, '내년 급여총액(성과급 포함)': S1 + B1, '내년 직원수': N1, '내년 1인당 급여': (S1 + B1) / N1,
        '내년 매출': REV1, '내년 영업이익률(%)': (OP_pre - dW) / REV1 * 100 if REV1 > 0 else np.nan,
        '내년 인건비율(%)': (S1 + B1) / REV1 * 100 if REV1 > 0 else np.nan,
        '비교 20곳 인건비율 중앙(%)': f.sr_ref * 100,
        # 위치
        '비교군 인상률 가정': g_peer,
        '지금 순위(마지막 해)': _rank(w_now, pw), '내년 예상 순위': _rank(w_next, pw_next),
        '지금 임금 차이(%)': (w_now / med_now - 1) * 100, '내년 예상 임금 차이(%)': (w_next / med_next - 1) * 100,
    })


def compare_offers(ctx, firm, union, company, **plan):
    """노조안 vs 회사안: 각 안 = dict(base_raise=…, bonus=…). 인원·매출·비교군 인상률(plan)은 두 안에 똑같이.
    두 열 + 차이(노조안 − 회사안)."""
    a = pay_plan(ctx, firm, **union, **plan)
    b = pay_plan(ctx, firm, **company, **plan)
    rng = negotiation_range(ctx, firm, peer_raise=plan.get('peer_raise'))
    for x in (a, b):                                              # 기능 2: 안이 협상 구간의 어디에 있는지
        x['협상 구간 하한'], x['협상 구간 상한'] = rng['하한'], rng['상한 표시']
        x['구간 위치'] = range_position(x['기본급 인상률'], rng)
    out = pd.DataFrame({'노조안': a, '회사안': b})
    is_num = out['노조안'].map(lambda v: isinstance(v, (int, float, np.floating)) and not isinstance(v, (bool, np.bool_)))
    out['차이(노조안 − 회사안)'] = (pd.to_numeric(out['노조안'], errors='coerce')
                                - pd.to_numeric(out['회사안'], errors='coerce')).where(is_num)
    return out


def load_forecast(path):
    """노트북 6-9의 예측 결과(6_9_예측결과_2025.csv)를 기업고유코드(8자리) 기준으로 읽는다."""
    fc = pd.read_csv(path, encoding='utf-8-sig', dtype={'기업고유코드': str})
    return fc.set_index('기업고유코드')


FORECAST_CASES = [('P10', '나쁜 쪽(P10)'), ('P50', '중앙(P50)'), ('P90', '좋은 쪽(P90)')]


def pay_plan_forecast(ctx, firm, fc, base_raise=0.0, bonus=0.0, headcount=0.0, sales_growth=None, peer_raise=None,
                      c=OVERHEAD_C, c_base=OVERHEAD_C_BASE):
    """인상안 × 다음 해 예측 범위 (기능 4-3). 인상안 비용은 pay_plan과 같고, 지급 전 영업이익만 모델 예측으로 바꾼다.
    - 내년 매출 = 매출 × (1 + 매출 증가율). sales_growth=None이면 모델의 매출 성장 P50 (로그 변화 → 증가율)
    - 지급 전 영업이익(경우별) = 내년 매출 × 예측 영업이익률 P10·P50·P90 (모델은 인상 효과를 넣지 않은 '지금 방식대로'의 예측)
    - 범위 예측은 여력 제약이 아니고 마지막 해 매출 > 0인 기업만 있다. 없으면 빈 표
    반환: 경우 3줄(나쁜 쪽·중앙·좋은 쪽) 표. attrs: 다음 해 적자 확률(모델 B), 매출 성장 범위"""
    if firm not in fc.index or not bool(fc.loc[firm, '범위예측_대상']):
        out = pd.DataFrame()
        out.attrs['안내'] = '범위 예측 대상이 아님 (여력 제약이거나 마지막 해 매출 없음). 다음 해 적자 확률만 참고'
        out.attrs['다음 해 적자 확률'] = fc.loc[firm, '다음해_적자확률'] if firm in fc.index else np.nan
        return out
    r = fc.loc[firm]
    g = np.expm1(r['매출 성장_P50']) if sales_growth is None else sales_growth
    plan = pay_plan(ctx, firm, base_raise=base_raise, bonus=bonus, headcount=headcount, sales_growth=g,
                    peer_raise=peer_raise, c=c, c_base=c_base)
    dW, REV1 = plan['회사 부담 증가(1년)'], plan['내년 매출']
    rows = []
    for q, label in FORECAST_CASES:
        m = r[f'영업이익률_{q}']
        pre = REV1 * m
        post = pre - dW
        rows.append({'경우': label, '예측 영업이익률(%)': m * 100, '내년 매출': REV1, '지급 전 영업이익': pre,
                     '회사 부담 증가': dW, '지급 후 영업이익': post,
                     '지급 후 영업이익률(%)': post / REV1 * 100 if REV1 > 0 else np.nan,
                     '비용÷영업이익(%)': dW / pre * 100 if pre > 0 else np.nan,
                     '지급 후 적자': bool(post < 0), '지급 때문에 적자 전환': bool(pre >= 0 and post < 0)})
    out = pd.DataFrame(rows).set_index('경우')
    out.attrs.update({'다음 해 적자 확률': r['다음해_적자확률'], '적용 매출 증가율': g,
                      '매출 증가율 범위(P10~P90)': (np.expm1(r['매출 성장_P10']), np.expm1(r['매출 성장_P90']))})
    return out


def profit_link_plan(ctx, firm, alpha=None, cap=None, floor=None, rate=PAY_RATE, c=OVERHEAD_C):
    """이익연동 전환 (기능 3): 급여의 rate를 고정으로 주던 성과급을 '영업이익의 α'로 바꾸면 어떻게 되나.
    - 기준은 진단과 같은 3년 연평균(급여·영업이익·매출·직원수 ÷ 3). 그래서 시작값 α*를 넣으면 연동 지급 = 고정 지급
    - alpha=None이면 시작값 α* / cap·floor: 급여 대비 상한·하한 (예: 0.10 = 급여의 10%)
    - 평상시 기준. 불황이 오면 지급액이 얼마로 바뀌는지는 기능 4 업계 불황 대비 점검(stress_test)에서만 본다 (11-21 결정)
    - 흑자일 때 회사 부담 ÷ 영업이익 = α × (1 + c)로 어느 회사나 같고, 회사마다 다른 것은 '급여 대비 지급률'(직원 몫)
    - 과거 연도에 적용해 보는 계산은 하지 않음 (11-21 결정)"""
    f = ctx.firms.loc[firm]
    a = f['α*'] if alpha is None else alpha
    S, N, REV = f.S_avg, f.N_avg, f.REV_avg
    OP = f.OP_avg
    fixed = rate * S
    pay = a * max(OP, 0) if pd.notna(OP) and pd.notna(a) else np.nan
    if pd.notna(pay) and floor is not None:
        pay = max(pay, floor * S)
    if pd.notna(pay) and cap is not None:
        pay = min(pay, cap * S)
    return pd.Series({
        '적용 비율(영업이익 대비)': a, '상한(급여 대비)': cap, '하한(급여 대비)': floor,
        '영업이익(3년 연평균)': OP,
        '고정 지급(급여 대비 rate)': fixed, '연동 지급': pay, '연동 ÷ 고정': pay / fixed if fixed > 0 else np.nan,
        '급여 대비 지급률(%)': pay / S * 100 if S > 0 else np.nan,
        '1인당 연동 지급': pay / N if N > 0 else np.nan, '1인당 고정 지급': fixed / N if N > 0 else np.nan,
        '회사 부담(연동)': pay * (1 + c) if pd.notna(pay) else np.nan,
        '연동 부담 ÷ 영업이익(%)': pay * (1 + c) / OP * 100 if pd.notna(pay) and OP > 0 else np.nan,
        '고정 부담 ÷ 영업이익(%)': fixed * (1 + c) / OP * 100 if OP > 0 else np.nan,
        '0원 지급': bool(pd.notna(OP) and OP <= 0 and floor is None),
    })


# =====================================================================
# 7-d. 기능 4 — 업계 불황 대비 점검(stress_test): 인상안·이익연동 규칙이 불황에서도 버티나 (결정표 12장)
#      업황 충격은 이 기능에서만 쓴다. 진단·인상 결정·이익연동 전환은 평상시 기준 (11-21 결정)
# =====================================================================
def _link_pay(alpha, op, s, cap, floor):
    pay = alpha * max(op, 0) if pd.notna(op) and pd.notna(alpha) else np.nan
    if pd.notna(pay) and floor is not None:
        pay = max(pay, floor * s)
    if pd.notna(pay) and cap is not None:
        pay = min(pay, cap * s)
    return pay


def scenarios(ctx, firm):
    """이 기업이 고를 수 있는 업황 시나리오 목록. 기준 연도와 같은 해의 사건은 빼고(이미 숫자에 반영됨),
    사건카탈로그에서 '이름 붙여 제공'인 우리 업종 사건만 이름을 붙인다."""
    f = ctx.firms.loc[firm]
    end, ind2 = ctx.end, int(f.ind2)
    out = [dict(경우=f'{k} ({y})', 종류='공통 사건', 연도=y, 근거='공통 시나리오') for k, y in SHOCK_COMMON.items() if y < end]
    cat = ctx.catalog
    if cat is not None:
        com = cat[cat['기능4 선택지'].eq('공통 시나리오 후보') & cat.연도.lt(end)]
        for _, r in com.iterrows():
            out.append(dict(경우=f'{r.사건명} ({r.연도})', 종류='공통 사건', 연도=int(r.연도), 근거=f'{r.확인수준} (공통 시나리오 후보)'))
        mine = cat[cat.중분류코드.eq(str(ind2)) & cat['기능4 선택지'].str.startswith('이름 붙여') & cat.연도.lt(end)]
        for _, r in mine.iterrows():
            tag = ' (일부 근거)' if r.확인수준 == '부분확인' else ''
            out.append(dict(경우=f'{r.사건명} ({r.연도}){tag}', 종류='우리 업종 사건', 연도=int(r.연도), 근거=r.확인수준))
    t2 = ctx.shocks['중분류']
    ser = t2[(t2.index.get_level_values(0) == ind2) & (t2.기업수 >= SHOCK_MIN_FIRMS)].이익률변화
    ser = ser[ser.index.get_level_values(1) < end]
    if len(ser):
        y = int(ser.idxmin()[1])
        named = [o for o in out if o['종류'] == '우리 업종 사건' and o['연도'] == y]
        if named:                                   # 같은 해의 이름 붙은 사건이 있으면 한 줄로 합침
            named[0]['경우'] += ' · 우리 업종 최악의 해'
        else:
            out.append(dict(경우=f'우리 업종 최악의 해 ({y})', 종류='최악의 해', 연도=y, 근거='데이터'))
    return out


def stress_test(ctx, firm, fc=None, base_raise=0.0, bonus=0.0, headcount=0.0, sales_growth=0.0, alpha=None, cap=None,
                floor=None, severity='중앙', with_sales=True, custom=None, rate=PAY_RATE, c=OVERHEAD_C, c_base=OVERHEAD_C_BASE):
    """기능 4 업계 불황 대비 점검: 기능 2의 인상안과 기능 3의 이익연동 규칙을 그대로 받아, 여러 미래에서 어떻게 되는지 한 표로.
    경우: 평상시(기능 2·3의 결과) / 모델 예측 P50·P10(fc가 있고 범위 예측 대상일 때) / 공통 사건 / 우리 업종 사건 / 최악의 해 / 직접 입력
    - 사건 충격: 그 업종이 그해 실제로 겪은 영업이익률 변화(Δm)와 매출 변화(Δr)를 적용 (severity: '중앙' 또는 '하위25')
        인상안:   내년 매출' = 내년 매출 × (1 + Δr),  지급 전 영업이익 = 내년 매출' × (지금 영업이익률 + Δm)
        이익연동: 연평균 매출 × (1 + Δr) × (연평균 영업이익률 + Δm)에 α (상한·하한)
      with_sales=False면 Δr = 0 (영업이익률만)
    - 모델 예측: 내년 매출 = 매출 × (1 + 모델 매출 성장 P50), 지급 전 영업이익 = 그 매출 × 예측 영업이익률 P50·P10
    - custom: dict(이익률=−0.03, 매출=−0.10) 처럼 직접 입력
    반환: 경우별 표. attrs: 기준 연도 경고, 강도, 다음 해 적자 확률"""
    f = ctx.firms.loc[firm]
    plan = pay_plan(ctx, firm, base_raise=base_raise, bonus=bonus, headcount=headcount, sales_growth=sales_growth,
                    c=c, c_base=c_base)
    link = profit_link_plan(ctx, firm, alpha=alpha, cap=cap, floor=floor, rate=rate, c=c)
    dW, REV1 = plan['회사 부담 증가(1년)'], plan['내년 매출']
    m_T = f.OP_T / f.REV_T if f.REV_T > 0 else np.nan
    m_avg = f.OP_avg / f.REV_avg if f.REV_avg > 0 else np.nan
    a = link['적용 비율(영업이익 대비)']
    fixed = link['고정 지급(급여 대비 rate)']

    def row(name, kind, yr, basis, rev1, op_pre, op_avg, dm=np.nan, dr=np.nan, unit=''):
        post = op_pre - dW
        pay = _link_pay(a, op_avg, f.S_avg, cap, floor)
        return {'경우': name, '종류': kind, '연도': yr, '근거': basis, '충격 단위': unit,
                '영업이익률 변화(%p)': dm * 100 if pd.notna(dm) else np.nan, '매출 변화(%)': dr * 100 if pd.notna(dr) else np.nan,
                '내년 매출': rev1, '지급 전 영업이익': op_pre, '인상안 회사 부담': dW, '지급 후 영업이익': post,
                '지급 후 영업이익률(%)': post / rev1 * 100 if rev1 > 0 else np.nan,
                '비용÷영업이익(%)': dW / op_pre * 100 if op_pre > 0 else np.nan,
                '지급 때문에 적자 전환': bool(op_pre >= 0 and post < 0), '지급 후 적자': bool(post < 0),
                '이익연동 지급': pay, '이익연동 ÷ 고정': pay / fixed if fixed > 0 else np.nan}

    rows = [row('평상시', '평상시', ctx.end, '기능 2·3의 결과', REV1, plan['지급 전 영업이익(내년)'], f.OP_avg)]
    if fc is not None and firm in fc.index and bool(fc.loc[firm, '범위예측_대상']):
        r = fc.loc[firm]
        rev_m = f.REV_T * (1 + headcount * 0) * np.exp(r['매출 성장_P50'])
        for q, label in [('P50', '모델 중앙(P50)'), ('P10', '모델 나쁜 쪽(P10)')]:
            m = r[f'영업이익률_{q}']
            rows.append(row(label, '모델 예측', ctx.end + 1, '노트북 6장 모델 D', rev_m, rev_m * m, f.REV_avg * m))

    def apply(name, kind, yr, basis, dm, dr, unit):
        dr = dr if with_sales else 0.0
        if pd.isna(dm):
            return
        rev1 = REV1 * (1 + dr)
        op_avg = f.REV_avg * (1 + dr) * (m_avg + dm)
        rows.append(row(name, kind, yr, basis, rev1, rev1 * (m_T + dm), op_avg, dm, dr, unit))

    for sc in scenarios(ctx, firm):
        sh = firm_shock(ctx.shocks, int(f.ind2), f.sec, sc['연도'], severity)
        apply(sc['경우'], sc['종류'], sc['연도'], sc['근거'], sh['이익률변화'], sh['매출변화'], f"{sh['단위']} {sh['기업수']}곳")
    if custom:
        apply('직접 입력', '직접 입력', None, '사용자 입력', custom.get('이익률', 0.0), custom.get('매출', 0.0), '')
    out = pd.DataFrame(rows).set_index('경우')
    out.attrs['강도'] = '업종의 보통 회사(중앙)' if severity != '하위25' else '업종에서 많이 맞은 회사(하위 25%)'
    out.attrs['매출 충격'] = with_sales
    if bool(f['기준연도 업종 충격']):
        out.attrs['기준 연도 경고'] = f'{ctx.end}년이 이미 이 업종의 큰 충격 해라, 그 위에 충격을 더 얹은 결과입니다'
    if fc is not None and firm in fc.index:
        out.attrs['다음 해 적자 확률'] = fc.loc[firm, '다음해_적자확률']
    return out


# =====================================================================
# 8. 부가 표시 — 급여 확인, WPS 참고값 (결정표 7장)
# =====================================================================
def pay_check(o):
    """W÷S 또는 공시 평균급여와 크게 다른 해가 있으면 '확인 필요'."""
    return np.where(o.ws_bad, f'확인 필요: W÷S가 {WS_RANGE[0]}~{WS_RANGE[1]} 밖',
                    np.where(o.avg_bad, '확인 필요: 공시 1인 평균급여와 25% 넘게 다름',
                             np.where(~o.ws_any & ~o.avg_any, '교차 확인 불가', '')))


WPS_VALUE_COLS = ['성과배분제 운영률(%)', '실제 지급 비율(%)', '변동급 비중 평균(%)',
                  '지급 수준 중앙(월 통상임금 대비 %)', '자발적 이직률 중앙(%)']


def prepare_wps(raw):
    """WPS 원자료 → 기업 전체 직원수·직원 구간·지표. 공공행정·금융 제외, 기업 전체 직원 10명 이상."""
    w = raw.copy()
    for c in w.columns:
        if c != 'ind':
            w[c] = pd.to_numeric(w[c], errors='coerce')
    for c in ['cq2104', 'cq3007']:
        w[c] = w[c].where(w[c] < 9000000)
    w['ind2'] = w.ind10.fillna(w.ind9)
    w = w[w.ind2.notna()].copy()
    w['sec'] = w.ind2.astype(int).map(ksic_section)
    w = w[w.aq2001.eq(2) & ~w.sec.isin(['K', 'O'])].copy()
    w['listed'] = w.aq2003.isin([1, 2, 3])
    firmfin = w.fpq1001.isin([1, 3])
    w['Nfirm'] = np.where(firmfin, w.fpq1011, np.where(w.aq1001.eq(1), w.epq1011, np.nan))
    w = w[w.Nfirm >= MIN_EMPLOYEES].copy()
    w['sz'] = pd.cut(w.Nfirm, SIZE_BANDS, labels=SIZE_LABELS).astype(str)
    w['ps'] = w.cq3001.eq(1).astype(float)
    w['paid'] = w.cq3002.eq(1).astype(float)
    w['turn'] = (w.epq8041 / w.epq4008).where(w.epq4008 > 0)
    w['turn'] = w.turn.where(w.turn <= 1.5)
    return w


def wps_table(w, end):
    """구간 끝 이하의 최근 두 조사 회차를 합쳐 대분류×직원구간, 대분류 기준값. 상장 10곳 이상이면 상장, 아니면 전체."""
    past = [x for x in WPS_WAVES if x <= end]
    if not past:
        return None, []
    pool = past[-2:]
    P = w[w.year.isin(pool)]
    rows = []
    for keys in (['sec', 'sz'], ['sec']):
        for k, d in P.groupby(keys):
            L = d[d.listed]
            src = L if len(L) >= WPS_MIN_SAMPLE else d
            if len(src) < WPS_MIN_SAMPLE:
                continue
            lv = src.cq3007.dropna()
            r = {'성과배분제 운영률(%)': src.ps.mean() * 100, '실제 지급 비율(%)': src.paid.mean() * 100,
                 '변동급 비중 평균(%)': src.cq2104.mean(),
                 '지급 수준 중앙(월 통상임금 대비 %)': lv.median() if len(lv) >= WPS_MIN_SAMPLE else np.nan,
                 '자발적 이직률 중앙(%)': src.turn.median() * 100,
                 '기준 표본': '상장' if len(L) >= WPS_MIN_SAMPLE else '전체(상장 표본 부족)'}
            kk = k if isinstance(k, tuple) else (k,)
            r['sec'] = kk[0]
            r['sz'] = kk[1] if len(kk) > 1 else '전체'
            rows.append(r)
    return pd.DataFrame(rows), pool


def attach_wps(o, wps_prepared, end):
    """기업마다 대분류×직원구간 값(없으면 대분류 값)을 붙인다. 개별 기업 값이 아니라 집단 참고값."""
    o = o.copy()
    cols = ['기준 표본'] + WPS_VALUE_COLS
    out_cols = ['WPS_단위'] + ['WPS_' + c for c in cols] + ['WPS_조사회차']
    T, pool = (None, []) if wps_prepared is None else wps_table(wps_prepared, end)
    if T is None or not len(T):
        for c in out_cols:
            o[c] = None
        return o
    Tc = T[T.sz != '전체'].set_index(['sec', 'sz'])
    Ts = T[T.sz == '전체'].set_index('sec')

    def one(r):
        if (r.sec, r.sz) in Tc.index:
            return pd.Series(['대분류×직원구간'] + Tc.loc[(r.sec, r.sz), cols].tolist())
        if r.sec in Ts.index:
            return pd.Series(['대분류'] + Ts.loc[r.sec, cols].tolist())
        return pd.Series([None] * (len(cols) + 1))

    o[out_cols[:-1]] = o.apply(one, axis=1)
    o['WPS_조사회차'] = '+'.join(map(str, pool))
    return o


# =====================================================================
# 9. 진단 문장
# =====================================================================
def sentence(r, years=YEARS_IN_WINDOW):
    s = []
    if r['임금 위치'] == '비교 불가':
        s.append(f"{r['name']}은(는) 비교할 회사가 부족해 임금 위치를 판정하지 않습니다({r['비교군 주의']}).")
    else:
        ind = IND2_NAME.get(int(r.ind2), str(r.ind2))
        same = int(r.n_same)
        s.append(f"{r['name']}의 1인당 급여는 {r.w / 1e4:,.0f}만 원으로, 같은 업종({ind}) 중심으로 매출·자산이 비슷한 "
                 f"20곳(같은 중분류 {same}곳 + 같은 대분류 {PEER_COUNT - same}곳)의 중앙값보다 {r['임금 차이(%)']:+.1f}%입니다"
                 f"(순위 {r.P * 100:.0f}%, 비교 20곳의 가운데 절반은 {r.ref25 / 1e4:,.0f}~{r.ref75 / 1e4:,.0f}만 원) → {r['임금 위치']}.")
        if r['비교군 주의']:
            s.append(f"주의: {r['비교군 주의']}.")
    if r['지급 여력'] == '여력 제약':
        s.append(f"지급 여력은 '여력 제약'({r['여력 사유']})이라, 급여 인상 계산보다 지급 여력 점검이 먼저입니다.")
    elif r['지급 여력'] == '판정 불가':
        s.append('매출 자료가 없어 지급 여력을 판정하지 않습니다.')
    else:
        s.append(f"지급 여력은 '{r['지급 여력']}'입니다({years}년 영업이익률 {r.opm * 100:.1f}%, "
                 f"같은 업종 중앙값 {r.opm_ind * 100:.1f}%).")
    if r['현금흐름 표시']:
        s.append(f"참고: {r['현금흐름 표시']}.")
    if r['지급 여력'] not in ('여력 제약', '판정 불가') and pd.notna(r['하락']):
        t = f"급여를 5% 올리면 회사 부담이 연 {eok(r.dW)} 늘어 영업이익률이 {r['하락']:.2f}%p 낮아집니다"
        t += (f"(마지막 해 영업이익의 {r['비용÷영업이익']:.0f}%)." if pd.notna(r['비용÷영업이익'])
              else '(마지막 해 영업이익이 적자라 영업이익 대비 비율은 계산하지 않음).')
        if pd.notna(r['g*']):
            t += f" 본전을 찾으려면 급여+영업이익+감가상각비 등이 {r['g*']:.1f}% 늘어야 합니다."
        else:
            t += f" 본전 기준선(g*)은 {r['g*표시']}라 숫자로 표시하지 않습니다."
        s.append(t)
    if r['급여 확인'].startswith('확인 필요'):
        s.append(f"자료 확인: {r['급여 확인']}.")
    return ' '.join(s)


# =====================================================================
# 10. 한 번에 계산
# =====================================================================
def compute(core, start, end, wps=None, rate=PAY_RATE, c=OVERHEAD_C):
    """구간 하나의 전체 결과 (기업 한 줄씩). wps는 load_wps 원자료(없으면 WPS 열은 빈칸).
    결과의 attrs: peers(비교군 목록)."""
    o = window(core, start, end)
    o, peers = wage_position(o)
    o = pay_capacity(o, end - start + 1)
    o = o.join(volatility(core, end))
    o = cost(o, rate, c)
    o = o.join(profit_share_rate(o, rate))
    o['급여 확인'] = pay_check(o)
    o = attach_wps(o, prepare_wps(wps) if wps is not None else None, end)
    o['진단문장'] = o.apply(sentence, axis=1, years=end - start + 1)
    o['구간'] = f'{start}~{end}'
    o['구간 연수'] = end - start + 1
    o.attrs.update(start=start, end=end, years=end - start + 1, peers=peers)
    return o


def to_table(B):
    """결과 표 (한글 열 이름). 노트북 6-8·MVP가 읽는 형식."""
    n_same = B.n_same.fillna(0).astype(int)
    out = pd.DataFrame({
        '구간': B['구간'], '구간 연수': B['구간 연수'], '기업고유코드': B.index, '기업명': B.name, '상장시장': B.mkt,
        '대분류': B.sec.map(SECTION_NAME), '중분류': B.ind2.map('{:02d}'.format) + ' ' + B.ind2.map(IND2_NAME).fillna(''),
        '직원수(구간 평균)': B.Nbar.round(0), '직원구간': B.sz,
        '1인당 급여(만원)': (B.w / 1e4).round(0), '비교 20곳 중앙(만원)': (B.ref / 1e4).round(0),
        '임금 차이(%)': B['임금 차이(%)'].round(1), '비교군 안 순위(0~1)': B.P.round(3), '임금 위치': B['임금 위치'],
        '참고 임금 구간 하단(만원)': (B.ref25 / 1e4).round(0), '참고 임금 구간 상단(만원)': (B.ref75 / 1e4).round(0),
        '비교군 중 같은 중분류(곳)': B.n_same,
        '비교군 구성': np.where(B.n_same.notna(), '같은 중분류 ' + n_same.astype(str) + '곳 + 같은 대분류 '
                           + (PEER_COUNT - n_same).astype(str) + '곳', ''),
        '비교군 매출 중앙÷자기 매출': B.rr.round(2), '비교군 주의': B['비교군 주의'],
        '영업이익률(%)': (B.opm * 100).round(1), '업종 중앙 영업이익률(%)': (B.opm_ind * 100).round(1),
        '업종 기준 단위': B['업종기준단위'], '이자보상비율 1 미만 연수': B.low_n, '적자 연도 수': B.lossyrs,
        '지급 여력': B['지급 여력'], '여력 사유': B['여력 사유'],
        '영업현금흐름 합(억원)': (B.CFO / 1e8).round(0), '현금흐름 표시': B['현금흐름 표시'],
        '인건비율 급여÷매출(%)': (B.sr * 100).round(1), '비교 20곳 인건비율 중앙(%)': (B.sr_ref * 100).round(1),
        '급여÷(급여+영업이익)': B.LS.round(2),
        '급여 증가율 변동성(%p)': (B.w_sd * 100).round(1), '영업이익률 평소 변동(%p)': (B.opm_sd * 100).round(1),
        '인상 계산': B['인상 계산'], '인상5%_회사 부담 증가(억원)': (B.dW / 1e8).round(1),
        '인상5%_영업이익률 하락(%p)': B['하락'].round(2), '인상5%_비용÷영업이익(%)': B['비용÷영업이익'].round(1),
        '인상5%_g*(%)': B['g*'].round(2), '인상5%_g* 계산값(%)': B['g*원값'].round(2), 'g* 표시': B['g*표시'],
        'D 상태(마지막 해)': B['D상태'], '인상5%_평소 변동 대비': B['평소변동대비'].round(2),
        **{c: (B[c].round(2) if B[c].dtype.kind == 'f' else B[c]) for c in B.columns
           if c.startswith('전환_')},
        **{c: B[c] for c in B.columns if c.startswith('WPS_')},
        '급여 확인': B['급여 확인'], '진단문장': B['진단문장']})
    return out.reset_index(drop=True)
