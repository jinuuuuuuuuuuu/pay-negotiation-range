"""기업개황 API(company.json): 업종코드, 법인구분(상장시장), 종목코드, 설립일, 결산월 등.
v2 비교군의 업종(KSIC 중분류)과 상장시장 빈칸(2023년 751곳)을 채우는 데 쓴다.

사용 예:
  python 06_collect_company_info.py --corps 기업목록.csv --out 결과폴더
출력: 결과폴더/기업개황.csv   열: corp, corp_name, stock_code, corp_cls, induty_code, est_dt, acc_mt, status
  corp_cls: Y=유가증권, K=코스닥, N=코넥스, E=기타(비상장)
호출량: 기업당 1건 (약 3,300건). 업종코드는 '현재' 기준 값 하나다(연도별 변경 이력은 없음).
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
ap.add_argument("--out", required=True)
ap.add_argument("--limit", type=int, default=18000)
a = ap.parse_args()

t = pd.read_csv(a.corps, dtype=str, encoding="utf-8-sig")
col = "기업고유코드" if "기업고유코드" in t.columns else "corp"
corps = sorted(t[col].dropna().unique())
d = os.path.join(a.out, "기업개황")
os.makedirs(d, exist_ok=True)
calls = 0
try:
    for i, c in enumerate(corps, 1):
        fp = os.path.join(d, c + ".json")
        if os.path.exists(fp):
            continue
        if calls >= a.limit:
            raise RateLimited("지정한 호출 한도 도달")
        j = dart_api.get_json("company.json", corp_code=c)
        calls += 1
        if j.get("status") == "net":
            continue
        json.dump(j, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
        if calls % 500 == 0:
            print(f"{i}/{len(corps)} 호출 {calls}", flush=True)
except RateLimited as e:
    print("한도로 중단:", e, "→ 같은 명령을 다시 실행하면 이어서 받습니다.")
rows = []
for c in corps:
    fp = os.path.join(d, c + ".json")
    if not os.path.exists(fp):
        continue
    j = json.load(open(fp, encoding="utf-8"))
    rows.append({"corp": c, "corp_name": j.get("corp_name"), "stock_code": j.get("stock_code"), "corp_cls": j.get("corp_cls"),
                 "induty_code": j.get("induty_code"), "est_dt": j.get("est_dt"), "acc_mt": j.get("acc_mt"), "status": j.get("status")})
pd.DataFrame(rows).to_csv(os.path.join(a.out, "기업개황.csv"), index=False, encoding="utf-8-sig")
print("완료: 기업개황.csv", len(rows), "행, 이번 호출", calls)
