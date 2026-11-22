# Pay Negotiation Range

**When a union asks for a bigger bonus or raise, where should HR start the negotiation?**
This project computes a *negotiation range* for any listed Korean company, using public DART filings (2,205 companies, 2023–2025), and shows it in a phone-sized web app.

- **Lower bound** = what peer companies actually raised pay (the argument labor can make)
- **Upper bound** = the raise at which the cost burden on operating profit equals the peers' burden (the argument management can make)
- A union offer and a company offer are plotted on top of that range, with their cost, next-year operating margin and position versus peers.

> Language note: the app, the documents and the code comments are in Korean. This section is the English overview; the Korean section below has the details.

## The app (4 features)

| # | Feature | Question it answers |
|---|---|---|
| 1 | **Diagnosis** | Where does this company stand against 20 peers (pay position, operating margin vs. industry)? |
| 2 | **Negotiation range** | Between which raise rates is a deal reasonable? Where do the union offer and the company offer fall? |
| 3 | **Profit-linked bonus** | What if a fixed 5%-of-payroll bonus became a share of operating profit? |
| 4 | **Future risk** | Next-year loss probability (reference only) and a *downturn check*: what if a past industry shock repeated? |

Live app: <https://jinuuuuuuuuuuu.github.io/pay-negotiation-range/>
(or run it locally, see `4_MVP/README.md`)

## What the evidence says

- Companies that pay 10% more have a 0.45 %p lower voluntary-quit rate (WPS panel); the bottom 20% by pay position quit at 17.8% vs. 12.7% for the top 20%. The within-company effect of raising pay was **not** confirmed.
- No evidence that bonuses raise productivity: bonus-paying firms were already growing faster *before* the bonus. Bonuses follow performance rather than cause it.
- Quit-rate and bonus data come from the Korea Labor Institute's Workplace Panel Survey (WPS). **The raw WPS data is not in this repository** (terms of use); only aggregated results are.

## Repository map

| Path | Contents |
|---|---|
| `4_MVP/` | The web app (static HTML/CSS/JS, no build step). `js/engine.js` mirrors `formula.py`; `tests/parity.test.mjs` checks both give identical numbers |
| `2_코드/` | `formula.py` (the single source of every formula), analysis notebook, tests (45) |
| `1_문서/` | Formula specification, decision log, event catalog, extra hypothesis tests (all Korean) |
| `3_결과/` | Result tables and figures (EDA, hypothesis tests, formulas, models) |

## Run it

```
# the app
cd 4_MVP
python -m http.server 8765        # open http://127.0.0.1:8765  (opening index.html directly will not load the data)
node tests/parity.test.mjs        # expect: 불일치 0개 (0 mismatches)

# the formulas (needs the DART panel CSV, see 2_코드/run_산술식.py for paths)
cd 2_코드
python -m pytest tests -q
```

## Contributing (team)

| File | Who | Notes |
|---|---|---|
| `4_MVP/index.html`, `css/app.css`, `js/app.js` | anyone | screens, wording, design. Design rules: `4_MVP/DESIGN.md` |
| `4_MVP/js/engine.js` | carefully | calculation logic. After editing, `node tests/parity.test.mjs` must report 0 mismatches |
| `4_MVP/data/*.json` | whoever has the DART panel | regenerate with `4_MVP/scripts/export_data.py`, never edit by hand |
| `2_코드/formula.py` | by pull request | change it first, then regenerate data and re-run both test suites |
| `PRODUCT.md`, `DESIGN.md` | after agreeing | product principles and design rules |

Pushing to `main` redeploys the app within a minute or two (GitHub Pages, `.github/workflows/pages.yml`). For anything bigger than a wording change, work on a branch and open a pull request so two people do not edit `app.js` at once.

---

# 한국어 설명

「성과급·임금 인상 협상 구간」: 성과급·임금 인상 요구를 받은 급여·노무 담당자가, 회사를 고르면 업계 비교군 20곳 기준으로 **협상 구간과 그 근거**를 휴대폰에서 확인하는 도구입니다. (Dart-B HR 학술제)

## 핵심 기능 4개
① **진단**: 업계 대비 임금 위치, 업계 대비 이익률 / ② **인상안 협상 구간**: 하한(업계 인상률)~상한(업계와 같은 부담 수준), 노조안·회사안 비교 / ③ **이익연동 전환**: 고정 성과급(급여 5%)을 영업이익 연동으로 바꾸면 / ④ **미래 위험**: 모델 예측(참고) + **업계 불황 대비 점검**

## 먼저 읽을 것
1. `1_문서/산술식_최종본.md`: 확정된 산술식. 맨 앞 "처음 보시는 분을 위한 설명"부터
2. `1_문서/결정표.md`: 규칙·상수의 출처, 결정과 진행 기록
3. `1_문서/사건카탈로그.md`: 2016~2025 업종별 업황 사건(데이터 충격 + 출처)
4. `1_문서/가설검정_추가_결과요약.md`: 임금 → 이직률(H7), 성과급 → 생산성(H8)
5. `1_문서/협상구간_설명_팀공유.md`: 협상 구간이 무엇이고 왜 이렇게 정했는지
6. `4_MVP/README.md`, `4_MVP/MVP_진행계획.md`: 앱의 구조와 진행 상황

## 폴더 구성
| 폴더 | 내용 |
|---|---|
| `1_문서` | 산술식 최종본, 결정표, 사건카탈로그, 추가 가설검정(사전 계획 + 결과 요약), 협상 구간 설명 |
| `2_코드` | `HR_코드_최종.ipynb`(EDA·가설검정·산술식·모델링, 실행 결과 포함), `formula.py`(산술식 정의), `wps_hypothesis.py`(H7·H8), `run_산술식.py`(결과 파일 만들기), `tests`(검산 테스트 45개) |
| `3_결과/1_EDA` | 노트북 1장 표·그림 |
| `3_결과/2_가설검정` | H1~H8 표·그림 (H7·H8은 WPS) |
| `3_결과/3_산술식` | 2023~2025 결과(2,205곳), 3년 구간 9개 결과, 비교군 20곳 목록, MVP 입력표, 업황 충격표, 사건카탈로그, 구간별 요약·안정성, 상식 점검, 근거 분석 결과 |
| `3_결과/4_모델링` | 모델 평가·3년 시나리오·통합 결과표, `6_9_예측결과_2025.csv`(미래 위험의 기업별 예측) |
| `4_MVP` | 휴대폰용 웹앱 |

## 실행 방법
**노트북 (Colab)**: `HR_코드_최종.ipynb`와 `formula.py`를 같은 폴더에 올리고, 노트북 0장의 `FORMULA_CANDIDATES`에 그 폴더를 적은 뒤 처음부터 실행합니다. 패널 CSV(`DART_패널_2015_2025.csv`)는 직접 구해야 합니다(저장소에 없음). 4장 H7·H8은 WPS 원자료(`WPS_통합.csv`, 이용 조건상 공유 금지)가 있어야 돌고, 없으면 그 두 가설만 건너뜁니다. 경로는 환경변수 `WPS_FILE`로 지정합니다.

**산술식 결과 다시 만들기 (PC)**
```
cd 2_코드
python run_산술식.py            # 2023~2025 + 3년 구간 9개 (환경변수 HR_DATA_DIR로 자료 위치 지정, 기본: 홈의 Downloads)
python run_산술식.py 2018 2022  # 한 구간
python -m pytest tests -q       # 검산 테스트
```

## 주의
- **팀 공식 숫자는 Colab에서 노트북을 한 번 다시 실행해 확정해 주세요.** 노트북 출력은 PC에서 실행한 것이라 pandas·scikit-learn 버전 차이로 H1-②와 6장 모델 수치가 소수점 셋째 자리에서 다를 수 있습니다(산술식 숫자는 같음).
- **WPS:** `WPS기준값_대분류x직원구간.csv`와 결과 파일의 `WPS_` 열은 WPS 원자료에서 만든 집계값입니다(10곳 미만 칸 제외). WPS 원자료는 넣지 않았습니다. 이용 조건은 한국노동연구원 안내를 따르세요.
- **DART:** 결과 파일에는 기업별 공시 수치가 들어 있습니다. API 키는 어디에도 없습니다.
- **PPT는 아직 고치지 않았습니다.** 고칠 곳은 `산술식_최종본.md` 7장에 있습니다.
- 근거 분석(f5, f8~f12)의 코드는 옛 계산 코드에 기대고 있어 넣지 않았습니다. 결과 파일만 `3_결과/3_산술식/근거_*`에 있습니다.
