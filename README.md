# 인상안 협상 구간 (Pay Negotiation Range)

**노조가 성과급·임금 인상을 요구했을 때, 어디서 협상을 시작해야 할까?**

DART 공시로 계산한 **협상 구간(하한~상한)**과 그 근거를 휴대폰에서 확인하는 웹앱입니다. 상장사 2,205곳(2023~2025년)에서 회사를 고르면, 같은 업계의 비슷한 회사 20곳을 기준으로 구간을 보여 줍니다.

**👉 [앱 열어 보기](https://jinuuuuuuuuuuu.github.io/pay-negotiation-range/)** (휴대폰에서 열어 보세요)

- **하한 = 업계 인상률** : 비슷한 회사들이 실제로 올린 비율. 이보다 낮으면 업계에 뒤처집니다. (노측이 내세울 근거)
- **상한 = 업계와 같은 부담 수준** : 인상 비용이 영업이익에서 차지하는 비중이 비교군과 같아지는 인상률. (사측이 내세울 근거)
- **노조안과 회사안**을 넣으면 구간 위에 점으로 찍히고, 비용·내년 영업이익률·업계 대비 임금 위치를 나란히 비교합니다.

> 상한은 "감당할 수 있는 한도"가 아니라 **업계 기준으로 맞춘 선**입니다. 여력이 있어도 경영진은 배당·재투자를 먼저 고려하기 때문에, 이 도구는 정답 한 점이 아니라 양측이 각자 내세울 수 있는 근거의 범위를 보여 줍니다.

## 핵심 기능 4개

| # | 기능 | 답하는 질문 |
|---|---|---|
| 1 | **진단** | 지금 우리 회사는 업계에서 어디인가? (업계 대비 임금 위치, 업계 대비 이익률) |
| 2 | **인상안 협상 구간** | 몇 %에서 몇 %까지가 협상 구간인가? 노조안·회사안은 어디에 있는가? |
| 3 | **이익연동 전환** | 고정 성과급(급여 5%)을 영업이익 연동으로 바꾸면 어떻게 되는가? |
| 4 | **미래 위험** | 다음 해 적자 확률(참고용), **업계 불황 대비 점검**: 과거의 불황이 다시 오면? |

## 데이터가 말해 주는 것

- 임금이 10% 높은 회사는 정규직 **자발적 이직률이 0.45%p 낮았습니다.** 업계 대비 임금 위치 하위 20% 회사의 이직률은 17.8%, 상위 20%는 12.7%입니다. 다만 같은 회사가 임금을 올렸을 때 이직이 줄어드는지는 **확인되지 않았습니다.** (WPS 사업체패널 2015~2023)
- **성과급이 생산성을 올린다는 근거는 찾지 못했습니다.** 성과급을 준 회사는 주기 전에 이미 생산성이 더 늘어 있었습니다. 성과급은 성과를 뒤따라 지급됩니다.
- 이직·성과급 자료는 한국노동연구원 사업체패널조사(WPS)에서 왔고, **원자료는 이 저장소에 없습니다**(이용 조건). 집계한 결과만 있습니다.
- 다음 해 적자 확률 모델은 적자 해를 가려내는 정확도가 높지 않아(AUC 0.66) 참고 지표로만 씁니다.

## 폴더 구성

| 폴더 | 내용 |
|---|---|
| `4_MVP` | **휴대폰용 웹앱** (순수 HTML/CSS/JS, 빌드 도구 없음). `js/engine.js`는 `formula.py`의 계산을 옮긴 것이고, `tests/parity.test.mjs`가 두 결과가 같은지 검사합니다 |
| `2_코드` | `formula.py`(모든 산술식의 단일 출처), 분석 노트북, 가설검정 모듈, 검산 테스트 45개 |
| `1_문서` | 산술식 최종본, 결정표, 업황 사건 카탈로그, 추가 가설검정, 협상 구간 설명 |
| `3_결과` | 결과 표와 그림 (EDA, 가설검정, 산술식, 모델링) |

먼저 읽을 문서
1. `1_문서/산술식_최종본.md` : 확정된 산술식. 맨 앞 "처음 보시는 분을 위한 설명"부터
2. `1_문서/협상구간_설명_팀공유.md` : 협상 구간이 무엇이고 왜 이렇게 정했는지
3. `1_문서/결정표.md` : 규칙과 상수의 출처, 결정 기록
4. `1_문서/가설검정_추가_결과요약.md` : 임금 → 이직률(H7), 성과급 → 생산성(H8)
5. `4_MVP/README.md`, `4_MVP/PRODUCT.md`, `4_MVP/DESIGN.md` : 앱의 구조, 제품 원칙, 디자인 기준

## 실행하기

**앱 (내 컴퓨터에서 확인)**
```
cd 4_MVP
python -m http.server 8765        # 브라우저에서 http://127.0.0.1:8765 (index.html을 파일로 직접 열면 데이터를 못 불러옵니다)
node tests/parity.test.mjs        # "불일치 0개"가 나와야 합니다
```

**산술식 (DART 패널 CSV가 있어야 합니다. 저장소에는 없음)**
```
cd 2_코드
python run_산술식.py              # 자료 위치는 환경변수 HR_DATA_DIR로 지정 (기본: 홈 폴더의 Downloads)
python -m pytest tests -q
```

**노트북 (Colab)**: `HR_코드_최종.ipynb`와 `formula.py`를 같은 폴더에 올리고, 0장의 `FORMULA_CANDIDATES`에 폴더를 적은 뒤 처음부터 실행합니다. 4장 H7·H8은 WPS 원자료(`WPS_통합.csv`)가 있어야 돌고, 없으면 그 두 가설만 건너뜁니다(환경변수 `WPS_FILE`).

## 팀원이 수정하려면

1. 저장소 관리자에게 공동 작업자로 초대받고 **초대를 수락**합니다.
2. `git clone https://github.com/jinuuuuuuuuuuu/pay-negotiation-range.git`
3. 자기 브랜치에서 고치고(`git switch -c 고칠-내용`) 확인한 뒤, 올리고(`git push`) Pull Request를 엽니다.
4. `main`에 합쳐지면 1~2분 뒤 앱 주소가 자동으로 바뀝니다 (`.github/workflows/pages.yml`).

| 파일 | 누가 | 주의 |
|---|---|---|
| `4_MVP/index.html`, `css/app.css`, `js/app.js` | 누구나 | 화면·문구·디자인. 디자인 규칙은 `4_MVP/DESIGN.md` |
| `4_MVP/js/engine.js` | 신중하게 | 계산 로직. 고친 뒤 `node tests/parity.test.mjs`가 불일치 0개여야 함 |
| `4_MVP/data/*.json` | DART 패널을 가진 사람 | 손으로 고치지 말고 `4_MVP/scripts/export_data.py`로 다시 만들기 |
| `2_코드/formula.py` | Pull Request로만 | 먼저 고친 뒤 데이터를 다시 만들고 두 테스트를 모두 다시 돌리기 |
| `PRODUCT.md`, `DESIGN.md` | 합의 후 | 제품 원칙과 디자인 기준 |

문구 한두 줄만 고칠 때는 GitHub 웹에서 파일을 열어 연필 아이콘으로 고치고 저장(Commit)해도 됩니다.

## 주의

- **팀 공식 숫자는 Colab에서 노트북을 한 번 다시 실행해 확정해 주세요.** 노트북 출력은 PC에서 실행한 것이라 pandas·scikit-learn 버전 차이로 가설검정 H1-②와 6장 모델 수치가 소수점 셋째 자리에서 다를 수 있습니다(산술식 숫자는 같음).
- **WPS:** `WPS기준값_대분류x직원구간.csv`와 결과 파일의 `WPS_` 열은 원자료에서 만든 집계값입니다(10곳 미만 칸 제외). 원자료는 넣지 않았습니다.
- **DART:** 결과 파일에는 기업별 공시 수치가 들어 있고, API 키는 어디에도 없습니다.
- 근거 분석(f5, f8~f12)의 코드는 옛 계산 코드에 기대고 있어 넣지 않았습니다. 결과 파일만 `3_결과/3_산술식/근거_*`에 있습니다.

---

# English summary

**When a union asks for a bigger bonus or raise, where should HR start the negotiation?**
This project computes a *negotiation range* for Korean listed companies from public DART filings (2,205 companies, 2023–2025) and shows it in a phone-sized web app: <https://jinuuuuuuuuuuu.github.io/pay-negotiation-range/>

- **Lower bound**: what peer companies actually raised pay (the argument labor can make).
- **Upper bound**: the raise at which the cost burden on operating profit equals the peers' burden (the argument management can make). It is a peer-based benchmark, not an affordability limit.
- A union offer and a company offer are plotted on the range, with cost, next-year operating margin and pay position versus peers.
- Evidence (WPS panel): firms paying 10% more have a 0.45 %p lower voluntary-quit rate (within-firm effect not confirmed); no evidence that bonuses raise productivity (bonuses follow performance). The raw WPS data is not in this repository.

Everything (app, documents, code comments) is in Korean. Layout: `4_MVP/` web app (static, no build step; `js/engine.js` is checked against `2_코드/formula.py` by `tests/parity.test.mjs`), `2_코드/` formulas, notebook and tests, `1_문서/` specification and decision log, `3_결과/` result tables. Pushing to `main` redeploys the app through GitHub Pages.
