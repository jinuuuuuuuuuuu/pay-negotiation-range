"""다중회사 주요계정 API(fnlttMultiAcnt): 한 번 호출에 최대 100개 기업의 매출액·영업이익·자산 등을 받는다.
연도당 약 34회 호출이면 3,300개 기업이 끝난다. (기업당 호출하는 전체 재무제표 API보다 100배 적게 호출)

사용 예:
  python 05_collect_main_accounts.py --corps 기업목록.csv --years 2020 2021 2022 2024 2025 --out 결과폴더
출력:
  결과폴더/주요계정/<연도>/batch_000.json ...   (원자료 그대로)
  결과폴더/주요계정_<연도>.csv   열: corp, year, fs_div(OFS=별도/CFS=연결), account, amount_won
  v2 산술식에는 fs_div == 'OFS' 이고 account == '영업이익' 인 행만 쓰면 된다.
주의: 공시되지 않은 기업은 응답에 없다(status 013). 연결만 있는 기업은 OFS 행이 없을 수 있다.
"""
import argparse
import json
import os
import sys

import pandas as pd

import dart_api
from dart_api import RateLimited

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--corps", required=True)
ap.add_argument("--years", nargs="+", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

t = pd.read_csv(a.corps, dtype=str, encoding="utf-8-sig")
col = "기업고유코드" if "기업고유코드" in t.columns else "corp"
corps = sorted(t[col].dropna().unique())
num = lambda v: pd.to_numeric(str(v).replace(",", ""), errors="coerce")
calls = 0
try:
    for y in a.years:
        d = os.path.join(a.out, "주요계정", y)
        os.makedirs(d, exist_ok=True)
        rows = []
        for b in range(0, len(corps), 100):
            fp = os.path.join(d, f"batch_{b // 100:03d}.json")
            if os.path.exists(fp):
                j = json.load(open(fp, encoding="utf-8"))
            else:
                j = dart_api.get_json("fnlttMultiAcnt.json", corp_code=",".join(corps[b:b + 100]), bsns_year=y, reprt_code="11011")
                calls += 1
                if j.get("status") == "net":
                    continue
                json.dump(j, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
            for r in j.get("list") or []:
                rows.append({"corp": r["corp_code"], "year": y, "fs_div": r.get("fs_div"), "account": r["account_nm"],
                             "amount_won": num(r.get("thstrm_amount")), "rcept_no": r.get("rcept_no")})
        pd.DataFrame(rows).to_csv(os.path.join(a.out, f"주요계정_{y}.csv"), index=False, encoding="utf-8-sig")
        print(y, "행", len(rows), "누적 호출", calls, flush=True)
except RateLimited as e:
    print("한도로 중단:", e, "→ 같은 명령을 다시 실행하면 이어서 받습니다.")
print("완료")
