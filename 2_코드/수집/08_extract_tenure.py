"""직원현황 API 원자료에서 평균 근속연수(년)를 추출한다.

공시 표기가 제각각이라 문자열을 연 단위 숫자로 바꾼다:
  "7년 9개월"→7.75, "9년2개월"→9.17, "6.2년"→6.2, "10개월"→0.83, "2년 5월"→2.42, "7"→7.0, "-"→결측
집계 규칙(직원수 교정과 같은 행 선택):
  1) 사업부문 합계 행(합계·총계·소계·전체·전사 등)이 있으면 그 행들만, 없으면 전체 행
  2) 그중 성별 합계 행이 있으면 그 행
  3) 선택된 행에 근속이 있으면 직원수 가중평균 → 방식 '합계행' 또는 '전체가중'
  4) 선택된 행에 근속이 없으면, 합계가 아닌 세부 행(부문·성별)의 직원수 가중평균 → '세부행가중'
  직원수가 없으면 단순평균. 0.1~40년 밖인 행(다른 칸 값 오입력 등)은 평균 전에 제외하고,
  모든 행이 범위 밖이면 결측 + 방식 '범위이상'. "1년 미만" 같은 범위 표기는 '해석불가'(결측).
사용: python 08_extract_tenure.py --out 평균근속연수_2015_2025.csv --src 2015=경로 2016=경로 ...
"""
import argparse, glob, json, os, re, sys
import numpy as np, pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
TOT = re.compile(r"합계|총계|소계|^계$|^전체|^전사|회사전체|^총$")
SEXTOT = re.compile(r"합계|^계$|전체")
P_YM = re.compile(r"(\d+(?:\.\d+)?)\s*년\s*(\d+(?:\.\d+)?)\s*개?월")
P_Y = re.compile(r"^(\d+(?:\.\d+)?)\s*년?$")
P_M = re.compile(r"^(\d+(?:\.\d+)?)\s*개?월(?:\d+일)?$")
P_YM_EN = re.compile(r"^(\d+)Y(\d+)M$", re.I)
P_DASH = re.compile(r"^(\d{1,2})-(\d{1,2})$")  # "17-11" = 17년 11개월
LO, HI = 0.1, 40.0


def parse_tenure(v):
    s = str(v if v is not None else "").strip().replace(",", "").replace(" ", " ")
    if s in ("", "-", "−", "None", "nan"): return np.nan
    s2 = re.sub(r"\s+", "", s)
    m = P_YM.search(s2)
    if m: return float(m.group(1)) + float(m.group(2)) / 12
    m = P_Y.match(s2)
    if m: return float(m.group(1))
    m = P_M.match(s2)
    if m: return float(m.group(1)) / 12
    m = P_YM_EN.match(s2)
    if m: return float(m.group(1)) + float(m.group(2)) / 12
    m = P_DASH.match(s2)
    if m and int(m.group(2)) <= 12: return float(m.group(1)) + float(m.group(2)) / 12
    return np.nan


def num(v):
    try: return float(str(v).replace(",", "").strip())
    except Exception: return np.nan


def wavg(rows):
    r = [x for x in rows if x["t"] == x["t"] and LO <= x["t"] <= HI]  # 범위 밖 행(다른 칸 값 오입력)은 평균에서 제외
    if not r: return np.nan
    w = [x["n"] for x in r]
    if all(n == n and n > 0 for n in w):
        return sum(x["t"] * x["n"] for x in r) / sum(w)
    return float(np.mean([x["t"] for x in r]))


def corp_tenure(L):
    rows = [{"seg": re.sub(r"\s", "", str(x.get("fo_bbm") or "")), "sex": re.sub(r"\s", "", str(x.get("sexdstn") or "")),
             "n": num(x.get("sm")), "t": parse_tenure(x.get("avrg_cnwk_sdytrn")), "raw": str(x.get("avrg_cnwk_sdytrn") or "")} for x in L]
    tot = [r for r in rows if TOT.search(r["seg"])]
    use = tot or rows
    st = [r for r in use if SEXTOT.search(r["sex"])]
    use = st or use
    t = wavg(use)
    if t == t: return t, ("합계행" if (tot or st) else "전체가중"), next((r["raw"] for r in use if r["t"] == r["t"]), "")
    detail = [r for r in rows if not TOT.search(r["seg"]) and not SEXTOT.search(r["sex"])]
    t = wavg(detail)
    if t == t: return t, "세부행가중", next((r["raw"] for r in detail if r["t"] == r["t"]), "")
    raws = [r["raw"] for r in rows if r["raw"].strip() not in ("", "-")]
    if any(r["t"] == r["t"] for r in rows): return np.nan, "범위이상", raws[0]
    return np.nan, ("해석불가" if raws else "미기재"), (raws[0] if raws else "")


ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--src", nargs="+", required=True, help="연도=폴더")
a = ap.parse_args()
out = []
for s in a.src:
    y, d = s.split("=", 1)
    fs = glob.glob(os.path.join(d, "*.json"))
    for f in fs:
        j = json.load(open(f, encoding="utf-8")); L = j.get("list") or []
        rec = {"기업고유코드": os.path.basename(f)[:-5], "사업연도": y}
        if L:
            t, how, raw = corp_tenure(L)
            rec.update({"평균근속연수(년)": round(t, 3) if t == t else np.nan, "근속_산출방식": how, "근속_원문예시": raw})
        else:
            rec.update({"평균근속연수(년)": np.nan, "근속_산출방식": "직원현황없음", "근속_원문예시": ""})
        out.append(rec)
    print(f"[{y}] 파일 {len(fs):,}")
df = pd.DataFrame(out)
df.to_csv(a.out, index=False, encoding="utf-8-sig")
print("저장:", a.out, "행", len(df))
