"""DART 기업·연도 패널(2015~2025) 만들기.

한 행 = 기업 × 연도. 변수마다 값 열 하나(+ 필요한 경우 상태 열 하나). 단위는 원. 결측은 0으로 채우지 않는다.
출처(변수별로 하나):
  키·업종·상장시장      : 기본 파일(24번)  → 비어 있으면 기업개황 API
  직원수·급여총액       : 직원현황 API 원자료, 사업부문 합계 행 규칙으로 교정 (교정_기본파일_직원수급여.csv)
  영업이익·매출·자산    : 다중회사 주요계정 API, 별도(OFS)  (주요계정_<연도>.csv)
  이자비용              : 재무 API 원자료 (이자비용_2015_2025.csv)
  감가·세금·대손·W      : 팀 v5.6 reparse 결과의 20번 파일 (연도별 내보내기)
사용: python build_panel.py [--out 폴더]
"""
import argparse, glob, os, sys, unicodedata
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
N = lambda s: unicodedata.normalize("NFC", s)
ap = argparse.ArgumentParser()
DL = os.environ.get("HR_DATA_DIR", os.path.join(os.path.expanduser("~"), "Downloads"))
ap.add_argument("--out", default=os.path.join(DL, "DART_패널"))
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
R = os.path.join(DL, "DART_재수집_20261114"); WORK = os.path.join(DL, "DART_패널작업")
# 2016년 주석 항목을 처리한 작업 폴더
TEAM_WORK = os.environ.get("TEAM_WORK_DIR", os.path.join(DL, "DART_2015_2019_TEAM_READY", "KPC_DART_work"))
num = lambda s: pd.to_numeric(s, errors="coerce")
rd = lambda p, **k: pd.read_csv(p, dtype=str, encoding="utf-8-sig", low_memory=False, **k)

# ---- 키 + 기본 파일
base = rd(R + r"\연도별_소형내보내기\24_기본24열_원문후보_추가_검증전.csv")  # 팀 24번 기본파일 사본
P = base[["기업고유코드", "사업연도", "기업명", "종목코드", "상장시장", "업종코드", "공시접수번호", "공시접수검토(1/0)"]].copy()
P = P.rename(columns={"공시접수검토(1/0)": "공시접수검토"})
assert not P.duplicated(["기업고유코드", "사업연도"]).any(), "기업·연도 중복"
yr = P["사업연도"].astype(int)
WPS = {2015: 2015, 2016: 2015, 2017: 2017, 2018: 2017, 2019: 2019, 2020: 2019, 2021: 2021, 2022: 2021, 2023: 2023, 2024: 2023, 2025: 2023}
P["WPS기준연도"] = yr.map(WPS)

# ---- 기업개황 (업종·상장시장 보충)
cp = os.path.join(R, "기업개황.csv")
if os.path.exists(cp):
    c = rd(cp).rename(columns={"corp": "기업고유코드"})[["기업고유코드", "corp_cls", "induty_code", "stock_code"]]
    c = c.drop_duplicates("기업고유코드")
    P = P.merge(c, on="기업고유코드", how="left")
    clsmap = {"Y": "코스피", "K": "코스닥", "N": "코넥스", "E": "기타"}
    P["상장시장"] = P["상장시장"].where(P["상장시장"].notna(), P["corp_cls"].map(clsmap))
    P["업종코드"] = P["업종코드"].where(P["업종코드"].notna(), P["induty_code"])
    P["종목코드"] = P["종목코드"].where(P["종목코드"].notna(), P["stock_code"])
    P = P.drop(columns=["corp_cls", "induty_code", "stock_code"])
P["업종코드_중분류"] = P["업종코드"].astype(str).str[:2].where(P["업종코드"].notna())

# ---- 직원수·급여총액 (교정본)
e = rd(R + r"\교정_기본파일_직원수급여.csv")[["기업고유코드", "사업연도", "직원수_교정", "급여총액_교정(원)", "직원현황_출처"]]
e = e.rename(columns={"직원수_교정": "직원수", "급여총액_교정(원)": "급여총액(원)", "직원현황_출처": "직원현황_상태"})
e["직원현황_상태"] = e["직원현황_상태"].replace({"24번_미검증": "미교정(24번값)"}).str.replace("API원자료_", "교정:", regex=False)
P = P.merge(e, on=["기업고유코드", "사업연도"], how="left")

# ---- 영업이익·매출·자산 (주요계정 OFS)
fin = []
for y in range(2015, 2026):
    p = os.path.join(R, f"주요계정_{y}.csv")
    if not os.path.exists(p): continue
    m = rd(p); m = m[(m["fs_div"] == "OFS") & m["account"].isin(["영업이익", "매출액", "자산총계"])]
    m = m.drop_duplicates(["corp", "account"]).pivot(index="corp", columns="account", values="amount_won").reset_index()
    m["사업연도"] = str(y); fin.append(m)
fin = pd.concat(fin).rename(columns={"corp": "기업고유코드", "영업이익": "영업이익(원)", "매출액": "매출액(원)", "자산총계": "자산총계(원)"})
P = P.merge(fin, on=["기업고유코드", "사업연도"], how="left")

# ---- 이자비용
ip = os.path.join(R, "이자비용_2015_2025.csv")
i = rd(ip)[["기업고유코드", "사업연도", "이자비용(원)", "이자비용_출처"]]
P = P.merge(i, on=["기업고유코드", "사업연도"], how="left")

# ---- 주석 항목 (팀 v5.6 20번)
KEEP_DIR = os.path.join(R, "연도별_소형내보내기")  # 작업 폴더 정리 후에도 쓰는 사본(20번 등 6개 파일/연도)
def note_path(y):
    kp = os.path.join(KEEP_DIR, str(y), "20_주석_기업별요약.csv")
    if os.path.exists(kp): return kp
    if y == 2019: return os.path.join(DL, "2019", "20_주석_기업별요약.csv")
    if y == 2018: return os.path.join(DL, "KPC_DART_2018", "KPC_DART_2018", "연도별내보내기", "2018", "20_주석_기업별요약.csv")  # 팀원 v5.6 재처리
    w = TEAM_WORK if y == 2016 else os.path.join(WORK, f"work_{y}")
    return os.path.join(w, "연도별내보내기", str(y), "20_주석_기업별요약.csv")
notes, missing_years = [], []
need = ["기업코드", "D_우선후보원", "D_우선자료상태", "T_우선후보원", "T_우선자료상태", "B_우선후보원", "B_우선자료상태", "W_잠정원", "W_구성요소완전성"]
for y in range(2015, 2026):
    p = note_path(y)
    if not os.path.exists(p):
        missing_years.append(y); continue
    n = rd(p); n = n[[c for c in need if c in n.columns]].copy(); n["사업연도"] = str(y); notes.append(n)
if notes:
    nn = pd.concat(notes).rename(columns={"기업코드": "기업고유코드", "D_우선후보원": "감가상각비(원)", "D_우선자료상태": "감가상각비_상태",
                                          "T_우선후보원": "세금과공과(원)", "T_우선자료상태": "세금과공과_상태", "B_우선후보원": "대손상각비(원)",
                                          "B_우선자료상태": "대손상각비_상태", "W_잠정원": "인건비총액W(원)", "W_구성요소완전성": "W_구성"})
    P = P.merge(nn.drop_duplicates(["기업고유코드", "사업연도"]), on=["기업고유코드", "사업연도"], how="left")
for c in ["감가상각비(원)", "감가상각비_상태", "세금과공과(원)", "세금과공과_상태", "대손상각비(원)", "대손상각비_상태", "인건비총액W(원)", "W_구성"]:
    if c not in P: P[c] = np.nan
for c in ["감가상각비", "세금과공과", "대손상각비"]:
    s = P[c + "_상태"]
    # 값이 없는데 원문 분석은 했던 기업 → '미확보', 분석 자체가 없으면 빈칸
    P[c + "_상태"] = s.where(P[c + "(원)"].notna(), pd.Series(["미확보"] * len(P), index=P.index).where(s.notna()))
# W 상태: 구성 + 급여총액 대비 0.8~2.0 검증 (단일 상태 열)
ratio = num(P["인건비총액W(원)"]) / num(P["급여총액(원)"])
w_txt = P["W_구성"].fillna("구성미확인").replace({"종업원급여합계_정의미확정": "종업원급여합계"}).astype(str)
w_sfx = pd.Series(np.where(ratio.between(0.8, 2.0), "", "·급여총액대비이상"), index=P.index)
P["인건비W_상태"] = (w_txt + w_sfx).where(P["인건비총액W(원)"].notna())
P = P.drop(columns=["W_구성"])

# ---- 표시 열 (행은 지우지 않음)
pay_pp = num(P["급여총액(원)"]) / num(P["직원수"])
P["플래그_지주회사"] = (P["업종코드"].astype(str).str.startswith("64992") | P["기업명"].astype(str).str.contains("지주|홀딩스")).astype(int)
P["플래그_급여이상"] = ((pay_pp < 2e7) | (pay_pp > 3e8)).astype(int)
P["플래그_직원10명미만"] = (num(P["직원수"]) < 10).astype(int)
# 단위 오독 등으로 의심되는 값: 감가상각비가 매출보다 크거나 음수, 이자비용이 자산의 50% 초과
dep, rev = num(P["감가상각비(원)"]), num(P["매출액(원)"])
P["플래그_감가이상"] = ((dep < 0) | ((dep > rev) & (rev > 0))).astype(int)
P["플래그_이자이상"] = ((num(P["이자비용(원)"]) / num(P["자산총계(원)"]).where(num(P["자산총계(원)"]) > 0)) > 0.5).astype(int)

cols = ["기업고유코드", "사업연도", "기업명", "종목코드", "상장시장", "업종코드", "업종코드_중분류", "WPS기준연도", "공시접수번호", "공시접수검토",
        "직원수", "급여총액(원)", "직원현황_상태", "영업이익(원)", "매출액(원)", "자산총계(원)", "이자비용(원)", "이자비용_출처",
        "감가상각비(원)", "감가상각비_상태", "세금과공과(원)", "세금과공과_상태", "대손상각비(원)", "대손상각비_상태", "인건비총액W(원)", "인건비W_상태",
        "플래그_지주회사", "플래그_급여이상", "플래그_직원10명미만", "플래그_감가이상", "플래그_이자이상"]
P = P[cols].sort_values(["기업고유코드", "사업연도"])
out = os.path.join(a.out, "DART_패널_2015_2025.csv")
P.to_csv(out, index=False, encoding="utf-8-sig")

# ---- 검증 리포트
L = [f"# DART 패널 검증 리포트\n", f"- 행 {len(P):,} / 기업 {P['기업고유코드'].nunique():,} / 연도 {P['사업연도'].min()}~{P['사업연도'].max()}",
     f"- (기업, 연도) 중복: {int(P.duplicated(['기업고유코드','사업연도']).sum())}",
     f"- 주석 내보내기가 없어 주석 항목이 비어 있는 연도: {missing_years}\n", "## 연도별 채움 (행 대비 %)\n"]
chk = ["직원수", "급여총액(원)", "영업이익(원)", "매출액(원)", "자산총계(원)", "이자비용(원)", "감가상각비(원)", "세금과공과(원)", "대손상각비(원)", "인건비총액W(원)", "업종코드", "상장시장"]
t = P.groupby("사업연도").apply(lambda g: pd.Series({"행": len(g), **{c: round(g[c].notna().mean() * 100) for c in chk}}), include_groups=False)
L.append("```\n" + t.to_string() + "\n```")
L.append("\n## 값 범위 점검")
for c in ["직원수", "급여총액(원)", "영업이익(원)", "감가상각비(원)", "인건비총액W(원)"]:
    s = num(P[c]).dropna(); L.append(f"- {c}: 최소 {s.min():,.0f} / 중앙 {s.median():,.0f} / 최대 {s.max():,.0f} / 음수 {int((s<0).sum())}")
L.append(f"- 1인당 급여(만원) 분위: {(pay_pp/1e4).quantile([.01,.25,.5,.75,.99]).round(0).to_dict()}")
L.append(f"- W 상태: {P['인건비W_상태'].value_counts().head(6).to_dict()}")
L.append(f"- 플래그: 지주회사 {int(P['플래그_지주회사'].sum())}, 급여이상 {int(P['플래그_급여이상'].sum())}, 직원10명미만 {int(P['플래그_직원10명미만'].sum())}, 감가이상 {int(P['플래그_감가이상'].sum())}, 이자이상 {int(P['플래그_이자이상'].sum())}")
L.append("\n## 알려진 기업 대조 (2023)")
for nm in ["삼성전자", "SK하이닉스", "현대자동차", "NAVER"]:
    r = P[(P["기업명"] == nm) & (P["사업연도"] == "2023")]
    if len(r): r = r.iloc[0]; L.append(f"- {nm}: 직원 {r['직원수']}, 급여총액 {r['급여총액(원)']}, 영업이익 {r['영업이익(원)']}, 감가 {r['감가상각비(원)']}, W {r['인건비총액W(원)']}")
open(os.path.join(a.out, "패널검증_리포트.md"), "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L[:12])); print(t.to_string())
print("저장:", out)
