"""한 연도(또는 여러 연도)를 순서대로 돌리는 실행기. 각 단계는 이미 받은 파일을 건너뛰므로 중단 후 다시 실행해도 된다.

사용 예:
  python run_year.py --corps 기업목록.csv --years 2024 2025 --out 결과폴더
  python run_year.py --corps 기업목록.csv --years 2024 --out 결과폴더 --steps 05 01 04     (일부 단계만)
  python run_year.py --corps 기업목록.csv --years 2024 --out 결과폴더 --plan               (호출량만 계산)

단계(기본 순서): 05 영업이익(적은 호출) → 01 직원현황 → 04 직원수 교정 → 02 원문 ZIP → 03 파싱 → 07 이자비용 → 06 기업개황(연도 무관, 한 번만)
기본 단계는 05 01 04 02 03 이다. 07(이자비용), 06(기업개황)은 --steps 에 직접 넣어야 돈다.
하루 호출 한도(키당 약 20,000건)를 넘길 것 같으면 --plan 으로 먼저 확인하고 연도를 나눠 실행한다.
"""
import argparse
import os
import subprocess
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--corps", required=True)
ap.add_argument("--years", nargs="+", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--steps", nargs="+", default=["05", "01", "04", "02", "03"])
ap.add_argument("--plan", action="store_true")
a = ap.parse_args()

t = pd.read_csv(a.corps, dtype=str, encoding="utf-8-sig")
col = "기업고유코드" if "기업고유코드" in t.columns else "corp"
n = t[col].nunique()
per_year = {"05": -(-n // 100), "01": n, "02": int(n * 2.2), "07": n, "06": 0, "04": 0, "03": 0}
if a.plan:
    tot = 0
    for y in a.years:
        c = sum(per_year[s] for s in a.steps if s != "06")
        tot += c
        print(f"{y}: 약 {c:,}건 ({', '.join(a.steps)})")
    if "06" in a.steps:
        tot += n
        print(f"기업개황(06): 약 {n:,}건 (한 번만)")
    print(f"합계 약 {tot:,}건 → 하루 한도(약 20,000건) 기준 약 {-(-tot // 18000)}일")
    sys.exit(0)


def run(script, *args):
    print("\n>>", script, *args, flush=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *args])
    if r.returncode != 0:
        sys.exit(f"{script} 실패(코드 {r.returncode}). 위 메시지를 확인하고 같은 명령을 다시 실행하세요.")


for s in a.steps:
    if s == "05":
        run("05_collect_main_accounts.py", "--corps", a.corps, "--years", *a.years, "--out", a.out)
    elif s == "01":
        run("01_collect_employees.py", "--corps", a.corps, "--years", *a.years, "--out", a.out)
    elif s == "04":
        dirs = [os.path.join(a.out, "직원현황", y) for y in a.years]
        run("04_fix_employees.py", "--dirs", *dirs, "--years", *a.years, "--out", os.path.join(a.out, "직원수_" + "_".join(a.years) + ".csv"))
    elif s == "02":
        for y in a.years:
            run("02_download_filings.py", "--corps", a.corps, "--year", y, "--out", a.out)
    elif s == "03":
        for y in a.years:
            sel = os.path.join(a.out, "원문ZIP", y, "선택결과.csv")
            if not os.path.exists(sel):
                print(f"{y}: 선택결과.csv 가 없어 03 단계를 건너뜁니다(02 단계를 먼저 실행).")
                continue
            tgt = os.path.join(a.out, f"파싱대상_{y}.csv")
            pd.read_csv(sel, dtype=str, encoding="utf-8-sig").query("rcept == rcept and rcept != ''")[["corp", "rcept"]].to_csv(tgt, index=False, encoding="utf-8-sig")
            run("03_parse_filings.py", os.path.join(a.out, "원문ZIP", y), tgt, os.path.join(a.out, f"재파싱_{y}.csv"))
    elif s == "07":
        run("07_collect_interest.py", "--corps", a.corps, "--years", *a.years, "--out", a.out)
    elif s == "06":
        run("06_collect_company_info.py", "--corps", a.corps, "--out", a.out)
    else:
        sys.exit("알 수 없는 단계: " + s)
print("\n완료")
