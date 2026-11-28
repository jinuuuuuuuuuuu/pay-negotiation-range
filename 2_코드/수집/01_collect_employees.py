"""직원현황 API(empSttus) 수집. 이미 받은 파일은 건너뛰므로 중단 후 다시 실행해도 된다.

사용 예:
  python 01_collect_employees.py --corps 기업목록.csv --years 2024 2025 --out 결과폴더
기업목록.csv: 열 이름이 '기업고유코드' 또는 'corp' 인 CSV (24번 파일 그대로 써도 됨)
출력: 결과폴더/직원현황/<연도>/<기업코드>.json
"""
import argparse
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
ap.add_argument("--limit", type=int, default=18000, help="이번 실행에서 호출할 최대 건수")
a = ap.parse_args()

t = pd.read_csv(a.corps, dtype=str, encoding="utf-8-sig")
col = "기업고유코드" if "기업고유코드" in t.columns else "corp"
corps = sorted(t[col].dropna().unique())
calls, stat = 0, {}
try:
    for y in a.years:
        d = os.path.join(a.out, "직원현황", y)
        os.makedirs(d, exist_ok=True)
        for i, c in enumerate(corps, 1):
            fp = os.path.join(d, c + ".json")
            if os.path.exists(fp):
                continue
            if calls >= a.limit:
                raise RateLimited("지정한 호출 한도 도달")
            j = dart_api.get_json("empSttus.json", corp_code=c, bsns_year=y, reprt_code="11011")
            calls += 1
            if j.get("status") == "net":
                continue          # 네트워크 오류: 파일을 만들지 않아 다음 실행에서 재시도
            import json
            json.dump(j, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
            stat[(y, j.get("status"))] = stat.get((y, j.get("status")), 0) + 1
            if calls % 500 == 0:
                print(f"{y} {i}/{len(corps)} 호출 {calls} {stat}", flush=True)
except RateLimited as e:
    print("한도로 중단:", e, "→ 같은 명령을 다시 실행하면 이어서 받습니다.")
print("완료", stat, "호출", calls)
