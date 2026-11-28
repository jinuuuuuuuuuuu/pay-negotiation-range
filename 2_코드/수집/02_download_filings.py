"""사업보고서 원문(document.xml ZIP) 내려받기. 연도별로 접수번호를 공시검색(list.json)으로 찾는다.

사용 예:
  python 02_download_filings.py --corps 기업목록.csv --year 2024 --out 결과폴더
출력:
  결과폴더/원문ZIP/<연도>/<접수번호>.zip
  결과폴더/원문ZIP/<연도>/선택결과.csv   (기업코드, 접수번호, 보고서명, 접수일, 상태)
선택 규칙: 보고서명에 '사업보고서'와 '(연도.' 가 들어간 공시 중 가장 늦게 접수된 것(정정 포함).
ZIP 하나에는 사업보고서 본문, 별도 감사보고서(_00760), 연결감사보고서(_00761)가 같이 들어 있다.
"""
import argparse
import os
import re
import sys
import zipfile

import pandas as pd

import dart_api
from dart_api import RateLimited

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("--corps", required=True)
ap.add_argument("--year", required=True, type=int)
ap.add_argument("--out", required=True)
ap.add_argument("--limit", type=int, default=18000)
a = ap.parse_args()
FULL_DOC_BYTES = 400_000     # 압축을 푼 가장 큰 문서가 이 크기 이상이면 재무제표 포함 본문으로 본다

t = pd.read_csv(a.corps, dtype=str, encoding="utf-8-sig")
col = "기업고유코드" if "기업고유코드" in t.columns else "corp"
corps = sorted(t[col].dropna().unique())
d = os.path.join(a.out, "원문ZIP", str(a.year))
os.makedirs(d, exist_ok=True)
res_fp = os.path.join(d, "선택결과.csv")
done = set(pd.read_csv(res_fp, dtype=str, encoding="utf-8-sig")["corp"]) if os.path.exists(res_fp) else set()
rows, calls = [], 0


def flush():
    global rows
    if rows:
        pd.DataFrame(rows).to_csv(res_fp, mode="a", index=False, encoding="utf-8-sig", header=not os.path.exists(res_fp))
        rows = []


try:
    for i, c in enumerate(corps, 1):
        if c in done:
            continue
        if calls >= a.limit:
            raise RateLimited("지정한 호출 한도 도달")
        j = dart_api.get_json("list.json", corp_code=c, bgn_de=f"{a.year}0101", end_de=f"{a.year + 1}1231",
                              pblntf_ty="A", page_count="100")
        calls += 1
        if j.get("status") == "net":
            continue
        cands = [x for x in (j.get("list") or [])
                 if "사업보고서" in x["report_nm"] and re.search(rf"\({a.year}\.", x["report_nm"])]
        rec = {"corp": c, "list_status": j.get("status"), "n_cand": len(cands), "rcept": "", "report_nm": "", "rcept_dt": "", "doc_status": ""}
        if cands:
            # 가장 늦은 접수본부터 받아 보고, 재무제표가 들어 있는(본문이 충분히 큰) 문서를 채택한다.
            # 기재정정본은 일부만 담긴 경우가 있어 더 이른 접수본으로 내려간다.
            cands.sort(key=lambda x: x["rcept_dt"], reverse=True)
            best = None
            for x in cands:
                fp = os.path.join(d, x["rcept_no"] + ".zip")
                if not os.path.exists(fp):
                    st, body = dart_api.get_zip("document.xml", rcept_no=x["rcept_no"])
                    calls += 1
                    if not body:
                        rec["doc_status"] = st.get("status")
                        continue
                    open(fp, "wb").write(body)
                size = max(i.file_size for i in zipfile.ZipFile(fp).infolist())
                if best is None or size > best[0]:
                    best = (size, x)
                if size >= FULL_DOC_BYTES:
                    break
            if best:
                size, x = best
                rec.update(rcept=x["rcept_no"], report_nm=x["report_nm"], rcept_dt=x["rcept_dt"], doc_status="000", doc_bytes=size)
                # 채택하지 않은 후보 ZIP은 지운다
                for y in cands:
                    if y["rcept_no"] != x["rcept_no"]:
                        p = os.path.join(d, y["rcept_no"] + ".zip")
                        if os.path.exists(p):
                            os.remove(p)
        rows.append(rec)
        if len(rows) >= 50:
            flush()
            print(f"{i}/{len(corps)} 호출 {calls}", flush=True)
except RateLimited as e:
    print("한도로 중단:", e, "→ 같은 명령을 다시 실행하면 이어서 받습니다.")
finally:
    flush()
print("완료 호출", calls)
