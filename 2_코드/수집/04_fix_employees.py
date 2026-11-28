"""직원현황 JSON(01번 결과 또는 기존 API원본JSON/employees/<연도>)을 기업·연도별로 집계한다.

규칙(중요): 사업부문에 '합계·총계·소계·전체·전사' 같은 합계 행이 있으면 그 행만 쓰고,
없으면 모든 행을 더한다. 합계 행과 부문 행을 함께 더하면 직원 수가 2배가 된다.
성별 합계 행('성별합계')이 있으면 그것만 쓴다.

사용 예:
  python 04_fix_employees.py --dirs 결과폴더/직원현황/2024 결과폴더/직원현황/2025 --years 2024 2025 --out 직원수_집계.csv
(--years 는 --dirs 와 같은 순서)
출력 열: corp, year, 직원수, 급여총액_원, 규칙, 단순합_직원수(비교용)
"""
import argparse
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--dirs", nargs="+", required=True)
ap.add_argument("--years", nargs="+", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

TOT = re.compile(r"합계|총계|소계|^계$|^전체|^전사|회사전체|^총$")


def num(v):
    if v in (None, "-", ""):
        return np.nan
    return pd.to_numeric(str(v).replace(",", "").strip(), errors="coerce")


def agg(rows):
    d = pd.DataFrame(rows)
    d["seg"] = d["fo_bbm"].fillna("").astype(str).str.replace(r"\s", "", regex=True)
    d["sex"] = d["sexdstn"].fillna("").astype(str).str.replace(r"\s", "", regex=True)
    d["n"] = d["sm"].map(num)
    d["s"] = d["fyer_salary_totamt"].map(num)
    t = d[d["seg"].str.contains(TOT)]
    use = t if len(t) else d
    st = use[use["sex"].str.contains(r"합계|^계$|전체")]
    if len(st):
        use = st
    return {"직원수": use["n"].sum(min_count=1), "급여총액_원": use["s"].sum(min_count=1),
            "규칙": ("합계행" if len(t) else "전체합") + ("+성별합계" if len(st) else ""),
            "단순합_직원수": d["n"].sum(min_count=1)}


out = []
for dr, y in zip(a.dirs, a.years):
    for fp in glob.glob(os.path.join(dr, "*.json")):
        j = json.load(open(fp, encoding="utf-8"))
        rows = j.get("list") or []
        rec = {"corp": os.path.basename(fp)[:-5], "year": y, "status": j.get("status")}
        if rows:
            rec.update(agg(rows))
        out.append(rec)
df = pd.DataFrame(out)
df.to_csv(a.out, index=False, encoding="utf-8-sig")
print("저장:", a.out, "행", len(df))
if "단순합_직원수" in df:
    dbl = df[(df["단순합_직원수"] / df["직원수"]).between(1.8, 2.2)]
    print("단순 합산하면 2배가 되는 기업:", len(dbl), "(합계 행 규칙이 적용된 곳)")
