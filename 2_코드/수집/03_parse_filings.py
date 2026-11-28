"""원문 ZIP 재파싱: 별도 감사보고서(없으면 사업보고서의 별도 재무제표)에서 감가상각비·W·세금과공과·대손상각비 추출

사용: python 03_parse_filings.py <원문ZIP폴더> <대상CSV(corp,rcept 열)> <출력CSV>
  대상CSV는 02번이 만든 선택결과.csv 에서 corp, rcept 열만 있으면 된다.
규칙:
  - ZIP 안 문서 우선순위: 별도 감사보고서 > 사업보고서의 별도 재무제표 구간. 연결감사보고서는 쓰지 않는다.
  - 성격별 비용 표는 표 안에 재고자산·원재료 행과 급여 행이 같이 있는 표로 판별한다(앞 문단 단어로 판별하지 않음).
  - 문서 순서상 첫 성격별 표만 쓴다. 단위(원/천원/백만원/억원)는 표 머리말·앞 문단에서 읽는다.
  - 감가상각비 상태(status): ok / 후보없음 / 기타표만 / 단위불명 / 별도문서없음
  - W = (종업원급여 또는 급여) + 같은 표의 퇴직급여 + 복리후생비   (w_status, W, W_form)
  - 세금과공과 T, 대손상각비 B: 성격별 표에 행이 있을 때만 값이 의미 있음(T_found, B_found).
    표는 찾았는데 행이 없으면 0으로 나오지만 '항목이 다른 계정에 합쳐졌을 수 있음'이므로 결측과 구분해서 쓸 것.
출력 열: dep(감가), amo(무형), dep_amo(합), src(표 종류), W, W_form, T, B, T_found, B_found, used_kind 등
검증 팁: W ÷ 직원현황 급여총액이 0.8~2.0 밖이면 원문 확인 대상.
"""
import re, sys, zipfile, html
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")

TITLE = re.compile(r"<TITLE[^>]*>(.*?)</TITLE>", re.S)
TABLE = re.compile(r"<TABLE\b.*?</TABLE>", re.S)
ROW = re.compile(r"<TR\b.*?</TR>", re.S)
CELL = re.compile(r"<(TD|TE|TH|TU)\b[^>]*>(.*?)</\1>", re.S)
NUM = re.compile(r"^\(?-?[\d,]+(\.\d+)?\)?$")
UNIT = re.compile(r"단\s*위\s*[:：]?\s*(원|천원|백만원|억원|USD|미국달러|달러|천달러|엔|위안)")
MULT = {"원": 1, "천원": 1e3, "백만원": 1e6, "억원": 1e8}


def decode_doc(b):
    """DART 원문은 utf-8로 선언돼 있어도 실제로는 cp949인 경우가 있다(2019~2021년 다수). 한글이 더 많이 읽히는 쪽을 쓴다."""
    u = b.decode("utf-8", errors="ignore")
    hu = len(re.findall("[가-힣]", u[:20000]))
    if hu >= 50:
        return u
    k = b.decode("cp949", errors="ignore")
    return k if len(re.findall("[가-힣]", k[:20000])) > hu else u


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def num(s):
    t = s.replace(" ", "")
    if not NUM.match(t) or t in ("-", ""):
        return None
    neg = t.startswith("(") or t.startswith("-")
    v = float(t.strip("()").replace(",", "").replace("-", "") or "nan")
    return -v if neg else v


def separate_ranges(raw):
    ts = [(m.start(), re.sub(r"\s", "", clean(m.group(1)))) for m in TITLE.finditer(raw)]
    ranges = []
    for i, (pos, t) in enumerate(ts):
        end = ts[i + 1][0] if i + 1 < len(ts) else len(raw)
        core = re.sub(r"^[\dIVX]+[\.\-]?\d*\.?", "", t).replace("(첨부)", "")
        if "연결" in core:
            continue
        if core in ("재무제표", "재무제표주석", "주석", "별도재무제표", "별도재무제표주석", "개별재무제표", "개별재무제표주석"):
            ranges.append((pos, end, core))
    return ranges


def classify(before, header):
    b = before[-1500:]
    if any(k in header for k in ("취득", "처분", "기초", "기말", "당기초", "전기초")):
        return "변동표"
    if "성격별" in b or "성격별" in header:
        return "성격별"
    if "현금흐름" in b or "영업활동" in header or "조정" in b[-400:] or "현금흐름" in header:
        return "현금흐름"
    if "판매비" in b or "판관비" in b:
        return "판관비"
    return "기타"


def parse(raw):
    out = []
    for s, e, core in separate_ranges(raw):
        seg = raw[s:e]
        for tm in TABLE.finditer(seg):
            tbl = tm.group(0)
            before = clean(seg[max(0, tm.start() - 2500): tm.start()])
            rows = [[clean(c[1]) for c in CELL.findall(r)] for r in ROW.findall(tbl)]
            if not rows:
                continue
            header = " ".join(" ".join(r) for r in rows[:2])
            um = UNIT.search(header) or UNIT.search(before[-600:])
            unit = um.group(1) if um else None
            kind = classify(before, header)
            if kind == "변동표":
                continue
            labels = " ".join(re.sub(r"\s", "", r[0]) for r in rows if r)
            nature_sig = bool(re.search(r"재고자산|원재료|원부재료|매입액|상품|원료", labels)) and bool(re.search(r"종업원급여|급여|인건비", labels))
            if kind == "성격별" and not nature_sig:
                kind = "기타"
            elif kind != "성격별" and nature_sig and re.search(r"감가상각", labels):
                kind = "성격별"
            for r in rows:
                if not r:
                    continue
                lab = re.sub(r"[\s　]", "", r[0])
                lab = re.sub(r"\(주석?[\d,\s]*\)|\(\*\d*\)|주\d+", "", lab)
                if len(lab) <= 30 and kind == "성격별":
                    tb = None
                    if re.search(r"세금과공과|제세공과|세금및공과|세금공과", lab):
                        tb = "T"
                    elif re.search(r"대손상각비|대손충당금|대손비용|매출채권손실충당금", lab) and "누계" not in lab:
                        tb = "B"
                    if tb:
                        vv = [num(c) for c in r[1:]]; vv = [v for v in vv if v is not None]
                        if vv:
                            out.append({"sec": core, "kind": kind, "label": lab, "val": vv[0], "unit": unit, "type": "TB_" + tb, "tid": (s, tm.start())})
                        continue
                if "누계" in lab or "손상" in lab or len(lab) > 30:
                    continue
                if kind == "성격별":
                    wt = None
                    if re.search(r"종업원급여|인건비", lab) and "퇴직" not in lab:
                        wt = "W_emp"
                    elif re.search(r"퇴직급여|퇴직연금|확정급여|확정기여", lab) and "부채" not in lab:
                        wt = "W_ret"
                    elif "복리후생" in lab:
                        wt = "W_wel"
                    elif re.search(r"^(급여|급료|임금|급여및상여|급료와임금|급여와상여|직원급여|상여금)", lab):
                        wt = "W_sal"
                    if wt:
                        vv = [num(c) for c in r[1:]]; vv = [v for v in vv if v is not None]
                        if vv:
                            out.append({"sec": core, "kind": kind, "label": lab, "val": abs(vv[0]), "unit": unit, "type": wt, "tid": (s, tm.start())})
                        continue
                isdep = "감가상각" in lab
                isamo = "무형자산상각" in lab or (("상각비" in lab) and ("무형" in lab))
                if not (isdep or isamo):
                    continue
                vals = [num(c) for c in r[1:]]
                vals = [v for v in vals if v is not None]
                if not vals:
                    continue
                comb = isdep and ("무형" in lab or "상각비및" in lab or "상각비와" in lab)
                out.append({"sec": core, "kind": kind, "label": lab, "val": abs(vals[0]), "unit": unit,
                            "type": "합산" if comb else ("감가" if isdep else "무형"), "tid": (s, tm.start())})
    return out


def choose_tb(cands):
    """성격별 비용 표(첫 표)에서 세금과공과·대손상각비. 표는 찾았는데 항목이 없으면 0(표 안에 없음), 표를 못 찾으면 결측."""
    df = pd.DataFrame([c for c in cands if c["kind"] == "성격별"])
    if df.empty:
        return {"tb_status": "성격별표없음"}
    df = df[df["unit"].isin(MULT.keys())]
    if df.empty:
        return {"tb_status": "단위불명"}
    df["won"] = df["val"] * df["unit"].map(MULT)
    g = df[df["tid"] == min(df["tid"])]
    def pick(t):
        x = g[g["type"] == t].drop_duplicates("label")
        return x["won"].sum() if len(x) else 0.0
    T, B = pick("TB_T"), pick("TB_B")
    return {"tb_status": "ok", "T": T, "B": B, "T_found": bool((g["type"] == "TB_T").any()), "B_found": bool((g["type"] == "TB_B").any()),
            "T_labels": "|".join(g[g["type"] == "TB_T"]["label"].unique())[:60], "B_labels": "|".join(g[g["type"] == "TB_B"]["label"].unique())[:60]}


def choose_w(cands):
    """성격별 비용 표(문서 순서상 첫 표)에서 W = 종업원급여(또는 급여) + 같은 표의 퇴직급여 + 복리후생비"""
    df = pd.DataFrame([c for c in cands if str(c["type"]).startswith("W_")])
    if df.empty:
        return {}
    df = df[df["unit"].isin(MULT.keys())]
    if df.empty:
        return {"w_status": "단위불명"}
    df["won"] = df["val"] * df["unit"].map(MULT)
    g = df[df["tid"] == min(df["tid"])]
    pick = lambda t: g[g["type"] == t].drop_duplicates("label")["won"].sum() if (g["type"] == t).any() else None
    emp, sal, ret, wel = pick("W_emp"), pick("W_sal"), pick("W_ret"), pick("W_wel")
    base = emp if emp is not None else sal
    if base is None:
        return {"w_status": "급여행없음"}
    W = base + (ret or 0) + (wel or 0)
    form = ("종업원급여" if emp is not None else "급여") + ("+퇴직" if ret is not None else "") + ("+복리" if wel is not None else "")
    return {"w_status": "ok", "W": W, "W_form": form, "W_labels": "|".join(g["label"].unique())[:120]}


def choose(cands):
    """표 종류 우선순위: 성격별 > 현금흐름 > 판관비(불완전 표시). 같은 종류 안에서는 첫 표만."""
    if not cands:
        return {}
    df = pd.DataFrame([c for c in cands if not str(c["type"]).startswith(("W_", "TB_"))])
    if df.empty:
        return {"status": "후보없음"}
    df = df[df["unit"].isin(MULT.keys())]
    if df.empty:
        return {"status": "단위불명"}
    df["won"] = df["val"] * df["unit"].map(MULT)
    for k in ("성격별", "현금흐름", "판관비"):
        g = df[df["kind"] == k]
        if g.empty:
            continue
        first_t = min(g["tid"])          # 문서 순서상 첫 표만 사용 (여러 표 합산 방지)
        g = g[g["tid"] == first_t]
        comb = g[g["type"] == "합산"]
        dep = g[g["type"] == "감가"]; amo = g[g["type"] == "무형"]
        # 같은 종류에서 중복 표(전기 재표시 등) 방지: 라벨별 첫 값만
        dep1 = dep.drop_duplicates("label")["won"].sum()
        amo1 = amo.drop_duplicates("label")["won"].sum()
        total = comb["won"].iloc[0] if len(comb) else dep1 + amo1
        return {"status": "ok", "src": k, "dep": dep1 if len(dep) else None, "amo": amo1 if len(amo) else None,
                "dep_amo": total, "n_rows": len(g), "labels": "|".join(g["label"].unique())[:120]}
    return {"status": "기타표만"}


if __name__ == "__main__":
    zdir, tgt, outp = sys.argv[1], sys.argv[2], sys.argv[3]
    t = pd.read_csv(tgt, dtype=str, encoding="utf-8-sig")
    res = []
    for i, r in enumerate(t.itertuples(), 1):
        rec = {"corp": r.corp, "rcept": r.rcept}
        try:
            z = zipfile.ZipFile(f"{zdir}\\{r.rcept}.zip")
            docs = []
            for nm in z.namelist():
                raw = decode_doc(z.read(nm))
                head = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw[:3000]))[:400]
                if re.search(r"연\s*결\s*감\s*사\s*보\s*고\s*서", head[:200]):
                    kind = "연결감사보고서"; pri = 9
                elif re.search(r"^\s*감사보고서|감\s*사\s*보\s*고\s*서", head[:120]) and "사업보고서" not in head[:120]:
                    kind = "감사보고서"; pri = 0
                elif "사업보고서" in head[:120] or "사 업 보 고 서" in head:
                    kind = "사업보고서"; pri = 1
                else:
                    kind = "기타"; pri = 5
                docs.append((pri, nm, kind, raw))
            docs.sort()
            rec["files"] = "|".join(k for _, _, k, _ in docs)
            rec["status"] = "별도문서없음"
            for pri, nm, kind, raw in docs:
                if pri >= 9:
                    continue
                rng = separate_ranges(raw)
                if not rng:
                    continue
                cands = parse(raw)
                got = choose(cands) or {"status": "후보없음"}
                gw = choose_w(cands)
                gt = choose_tb(cands)
                rec.update({"used_file": nm, "used_kind": kind, "sep_sections": len(rng), **got, **gw, **gt})
                if got.get("status") == "ok":
                    break
        except Exception as ex:
            rec["status"] = "오류:" + str(ex)[:40]
        res.append(rec)
        if i % 500 == 0:
            print(i, "/", len(t), flush=True)
    pd.DataFrame(res).to_csv(outp, index=False, encoding="utf-8-sig")
    print("완료", outp)
