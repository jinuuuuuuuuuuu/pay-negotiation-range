# 4_MVP — 휴대폰용 에이전트 MVP (정적 웹앱)

「성과급·임금」 에이전트의 기능 4개(진단 / 인상안 협상 구간 / 급여 기준 ↔ 이익 기준 환산 / 미래 위험)를 휴대폰 브라우저에서 돌리는 정적 웹앱입니다. 서버 없이 `data/*.json`을 읽고 `js/engine.js`가 계산합니다. 배포는 GitHub Pages 예정.

## 폴더
| 경로 | 내용 |
|---|---|
| `data/` | 앱이 읽는 데이터 (회사 2,205곳, 비교군, 예측, 업황 충격표, 사건카탈로그, 상수). `scripts/export_data.py`가 만듦 |
| `js/engine.js` | 계산 엔진. `2_코드/formula.py`의 기능 2~4 함수를 그대로 옮김 (출력 항목 이름도 같음) |
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
DART 패널 원자료(`Downloads/DART_패널`)가 필요합니다. WPS 원자료는 앱에 넣지 않습니다(결과의 WPS 참고값은 10곳 이상 칸의 집계뿐).

## 현재 상태 (2026-11-22)
- 1단계 데이터 내보내기 완료: firms 2.9MB(압축 508KB), forecast 738KB(240KB), peers 476KB(116KB) 외. 소수는 유효숫자 8자리(판정·문구 영향 0건, 숫자 최대 상대 차이 4e-6).
- 2단계 계산 엔진 완료: 98곳 × 입력 조합, 값 89,579개 불일치 0개. 일부러 틀린 값을 넣으면 잡아내는 것도 확인.
- 3~5단계 완료(11-22 오전 예약 작업): 화면 6개(`index.html`, `css/app.css`, `js/app.js`, `js/icons.js`), `PRODUCT.md`, `DESIGN.md`, `.impeccable/`(설정·방향 계약서·디자인 사이드카). 계산 일치 테스트 불일치 0개 유지.
- 다음: 6단계 배포(GitHub Pages) → 사용자 확인 필요. 자세한 상태는 `MVP_진행계획.md`

## 로컬에서 열기
```
cd 4_MVP
python -m http.server 8765
```
브라우저(또는 같은 와이파이의 휴대폰)에서 `http://127.0.0.1:8765/` (휴대폰은 PC의 IP 주소). `index.html`을 파일로 직접 열면 데이터 불러오기가 막히므로 꼭 서버로 연다.
