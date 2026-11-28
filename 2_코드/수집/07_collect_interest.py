"""전체 재무제표 API(fnlttSinglAcntAll, 별도 OFS)에서 이자비용을 모은다. 한계기업 판정(이자보상비율 = 영업이익 ÷ 이자비용,
3년 연속 100% 미만)에 필요한 다년 이자비용용이다.

사용 예:
  python 07_collect_interest.py --corps 기업목록.csv --years 2023 2024 2025 --out 결과폴더
출력:
  결과폴더/전체재무제표/<연도>/<기업코드>.json   (원자료)
  결과폴더/이자비용_<연도>.csv   열: corp, year, status, interest_expense_won, interest_paid_won, finance_cost_won, interest_best_won, interest_src
호출량: 기업·연도당 1건 (연도당 약 3,300건). 3년이면 약 10,000건.
추출 규칙:
  - interest_expense_won : 손익계산서의 '이자비용'(표준계정 ifrs-full_InterestExpense). 대부분의 기업은 손익계산서에 따로 적지 않는다.
  - interest_paid_won    : 현금흐름표의 '이자의 지급'(영업·재무활동 합산). 현금 기준이고 자본화 이자를 포함하는 근사치.
  - interest_best_won    : 위 둘 중 있는 값(손익계산서 우선). 한계기업 판정(영업이익 ÷ 이자비용)에는 이 열을 쓴다.
  - finance_cost_won     : 손익계산서의 '금융비용/금융원가'. 외환차손·파생손익 등이 섞여 이자비용보다 훨씬 클 수 있으므로(삼성전자 2024 약 12배)
    이자보상비율에 쓰면 안 된다. 기존 10번 파일의 interest_expense_candidate 는 이 금융비용이었다.
주의: 전체 재무제표 API는 별도(OFS)를 요청하며, 공시가 없거나 연결만 있는 기업은 status 013 이다.
"""
import argparse
import json
import os
import re
import sys

import pandas as pd

import dart_api
from dart_api import RateLimited

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--corps", required=True)
ap.add_argument("--years", nargs="+", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--limit", type=int, default=18000)
a = ap.parse_args()

t = pd.read_csv(a.corps, dtype=str, encoding="utf-8-sig")
col = "기업고유코드" if "기업고유코드" in t.columns else "corp"
corps = sorted(t[col].dropna().unique())
num = lambda v: pd.to_numeric(str(v).replace(",", ""), errors="coerce")


def pick(rows):
    """(손익계산서 이자비용, 현금흐름표 이자 지급액, 금융비용)"""
    ie, fc, paid = None, None, {}
    for r in rows:
        nm = re.sub(r"\s", "", r.get("account_nm", ""))
        v = num(r.get("thstrm_amount"))
        if pd.isna(v):
            continue
        aid = r.get("account_id", "")
        if r.get("sj_div") in ("IS", "CIS"):
            if (nm in ("이자비용", "이자비용(주석)") or aid == "ifrs-full_InterestExpense") and ie is None:
                ie = v
            if re.fullmatch(r"(금융비용|금융원가|금융손익비용)", nm) and fc is None:
                fc = v
        elif r.get("sj_div") == "CF":
            if aid.startswith("ifrs-full_InterestPaid") or re.fullmatch(r"이자의?(지급|지급액)|이자지급", nm):
                paid[aid + "|" + nm] = abs(v)      # 활동 구분(영업/재무)이 다른 행은 합산
    return ie, (sum(paid.values()) if paid else None), fc


calls = 0
try:
    for y in a.years:
        d = os.path.join(a.out, "전체재무제표", y)
        os.makedirs(d, exist_ok=True)
        rows = []
        for i, c in enumerate(corps, 1):
            fp = os.path.join(d, c + ".json")
            if os.path.exists(fp):
                j = json.load(open(fp, encoding="utf-8"))
            else:
                if calls >= a.limit:
                    raise RateLimited("지정한 호출 한도 도달")
                j = dart_api.get_json("fnlttSinglAcntAll.json", corp_code=c, bsns_year=y, reprt_code="11011", fs_div="OFS")
                calls += 1
                if j.get("status") == "net":
                    continue
                json.dump(j, open(fp, "w", encoding="utf-8"), ensure_ascii=False)
                if calls % 500 == 0:
                    print(f"{y} {i}/{len(corps)} 호출 {calls}", flush=True)
            ie, paid, fc = pick(j.get("list") or [])
            best = ie if ie is not None else paid
            rows.append({"corp": c, "year": y, "status": j.get("status"), "interest_expense_won": ie, "interest_paid_won": paid,
                         "finance_cost_won": fc, "interest_best_won": best,
                         "interest_src": "손익계산서 이자비용" if ie is not None else ("현금흐름표 이자지급" if paid is not None else "")})
        pd.DataFrame(rows).to_csv(os.path.join(a.out, f"이자비용_{y}.csv"), index=False, encoding="utf-8-sig")
        r = pd.DataFrame(rows)
        print(y, "기업", len(r), "| 손익 이자비용", int(r["interest_expense_won"].notna().sum()), "| 현금흐름 이자지급", int(r["interest_paid_won"].notna().sum()),
                  "| 둘 중 하나(interest_best)", int(r["interest_best_won"].notna().sum()), "| 금융비용만 있음", int((r["interest_best_won"].isna() & r["finance_cost_won"].notna()).sum()), flush=True)
except RateLimited as e:
    print("한도로 중단:", e, "→ 같은 명령을 다시 실행하면 이어서 받습니다.")
print("완료 호출", calls)
