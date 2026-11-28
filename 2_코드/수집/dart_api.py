"""OpenDART 호출 공통 모듈.

API 키는 환경변수 DART_API_KEY 또는 이 폴더(또는 현재 폴더)의 .env 파일에서 읽는다.
키는 코드·로그·출력에 남기지 않는다.
"""
import json
import os
import time
import urllib.parse
import urllib.request

BASE = "https://opendart.fss.or.kr/api/"
UA = {"User-Agent": "dart-collect-client/1.0"}
MIN_GAP = 0.15          # 호출 간격(초). 하루 한도는 키당 약 20,000건
_last = [0.0]


class RateLimited(Exception):
    """일일 한도 초과(status 020)"""


def _load_key():
    key = os.environ.get("DART_API_KEY")
    if key:
        return key.strip()
    here = os.path.dirname(os.path.abspath(__file__))
    for d in (here, os.getcwd()):
        p = os.path.join(d, ".env")
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                if line.startswith("DART_API_KEY="):
                    return line.strip().split("=", 1)[1]
    raise SystemExit("API 키가 없습니다. 환경변수 DART_API_KEY 설정 또는 .env 파일(.env.example 참고)을 만드세요.")


KEY = _load_key()


def _request(endpoint, params, retries=3):
    q = dict(params)
    q["crtfc_key"] = KEY
    url = BASE + endpoint + "?" + urllib.parse.urlencode(q)
    for i in range(retries):
        gap = time.time() - _last[0]
        if gap < MIN_GAP:
            time.sleep(MIN_GAP - gap)
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            _last[0] = time.time()
            return body
        except Exception as e:                      # 네트워크 오류는 재시도
            _last[0] = time.time()
            if i == retries - 1:
                return ("NET:" + str(e)[:150]).encode()
            time.sleep(2 * (i + 1))


def get_json(endpoint, **params):
    body = _request(endpoint, params)
    if body.startswith(b"NET:"):
        return {"status": "net", "message": body.decode()[:150]}
    j = json.loads(body.decode("utf-8"))
    if j.get("status") == "020":
        raise RateLimited(j.get("message"))
    return j


def get_zip(endpoint, **params):
    """(상태 dict, zip 바이트 또는 None)"""
    body = _request(endpoint, params)
    if body.startswith(b"NET:"):
        return {"status": "net", "message": body.decode()[:150]}, None
    if body[:2] == b"PK":
        return {"status": "000"}, body
    txt = body.decode("utf-8", errors="ignore")
    for code in ("020", "013", "014", "010", "011", "012", "100", "101", "800", "900"):
        if f"<status>{code}</status>" in txt:
            if code == "020":
                raise RateLimited(txt[:150])
            return {"status": code, "message": txt[:150]}, None
    return {"status": "999", "message": txt[:150]}, None
