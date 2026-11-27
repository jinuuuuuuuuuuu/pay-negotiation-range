# 4_MVP — 휴대폰용 에이전트 MVP (정적 웹앱)

「성과급·임금」 에이전트의 기능 4개(진단 / 인상안 협상 구간 / 급여 기준 ↔ 이익 기준 환산 / 미래 위험)를 휴대폰 브라우저에서 돌리는 정적 웹앱임, 서버 없이 `data/*.json`을 읽고 `js/engine.js`가 계산함, GitHub Pages로 배포함(`.github/workflows/pages.yml`)

## 폴더
| 경로 | 내용 |
|---|---|
| `data/` | 앱이 읽는 데이터 (회사 2,205곳, 비교군, 예측, 업황 충격표, 사건카탈로그, 상수), `scripts/export_data.py`가 만듦 |
| `js/engine.js` | 계산 엔진, `2_코드/formula.py`의 기능 2~4 함수를 그대로 옮김 (출력 항목 이름도 같음) |
| `scripts/export_data.py` | 최종본 `formula.py`로 계산해 `data/*.json` 생성 + `3_결과` CSV와 대조 |
| `scripts/make_golden.py` | `data/*.json`을 입력으로 `formula.py`를 돌려 정답 세트 `tests/golden.json` 생성 |
| `tests/parity.test.mjs` | JS 엔진이 정답 세트와 같은지 검사 |

## 다시 만들기 (formula.py나 결과가 바뀌었을 때)
```
cd 4_MVP/scripts
python export_data.py      # data/*.json, 끝에 "최종본 CSV와 대조: 모두 같음"이 나와야 함
python make_golden.py      # tests/golden.json
cd ..
node tests/parity.test.mjs # "불일치 0개"가 나와야 함
```
DART 패널 원자료(`Downloads/DART_패널`)가 필요함, WPS 원자료는 앱에 넣지 않음(결과의 WPS 참고값은 10곳 이상 칸의 집계뿐)

## 로컬에서 열기
```
cd 4_MVP
python -m http.server 8765
```
브라우저(또는 같은 와이파이의 휴대폰)에서 `http://127.0.0.1:8765/` (휴대폰은 PC의 IP 주소), `index.html`을 파일로 직접 열면 데이터 불러오기가 막히므로 꼭 서버로 연다
