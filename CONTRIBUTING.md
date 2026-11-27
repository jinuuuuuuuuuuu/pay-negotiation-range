# 팀원 수정 안내

## 수정 절차

1. 저장소 관리자에게 공동 작업자로 초대받고 초대를 수락함
2. `git clone https://github.com/jinuuuuuuuuuuu/pay-negotiation-range.git`
3. 자기 브랜치에서 고치고(`git switch -c 고칠-내용`) 확인한 뒤, 올리고(`git push`) Pull Request를 생성함
4. `main`에 합쳐지면 1~2분 뒤 앱 주소가 자동으로 바뀜 (`.github/workflows/pages.yml`)

문구 한두 줄만 고칠 때는 GitHub 웹에서 파일을 열어 연필 아이콘으로 고치고 저장(Commit)해도 됨

## 파일별 주의

| 파일 | 누가 | 주의 |
| --- | --- | --- |
| `4_MVP/index.html`, `css/app.css`, `js/app.js` | 누구나 | 화면·문구·디자인, 디자인 규칙은 `4_MVP/DESIGN.md` |
| `4_MVP/js/engine.js` | 신중하게 | 계산 로직, 고친 뒤 `node tests/parity.test.mjs`가 불일치 0개여야 함 |
| `4_MVP/data/*.json` | DART 패널을 가진 사람 | 손으로 고치지 말고 `4_MVP/scripts/export_data.py`로 다시 만들기 |
| `2_코드/formula.py` | Pull Request로만 | 먼저 고친 뒤 데이터를 다시 만들고 두 테스트를 모두 다시 돌리기 |
| `4_MVP/PRODUCT.md`, `4_MVP/DESIGN.md` | 합의 후 | 제품 원칙과 디자인 기준 |

## 노트북 (Colab)

`HR_코드_최종.ipynb`와 `formula.py`를 같은 폴더에 올리고, 0장의 `FORMULA_CANDIDATES`에 폴더를 적은 뒤 처음부터 실행함, 4장 H7·H8은 WPS 원자료(`WPS_통합.csv`)가 있어야 돌고, 없으면 그 두 가설만 건너뜀(환경변수 `WPS_FILE`)

## 주의

- 팀 공식 숫자는 Colab에서 노트북을 한 번 다시 실행해 확정함, 노트북 출력은 PC에서 실행한 것이라 pandas·scikit-learn 버전 차이로 가설검정 H1-②와 6장 모델 수치가 소수점 셋째 자리에서 다를 수 있음(산술식 숫자는 같음)
- `WPS기준값_대분류x직원구간.csv`와 결과 파일의 `WPS_` 열은 원자료에서 만든 집계값임(10곳 미만 칸 제외), 원자료는 넣지 않음
- 결과 파일에는 기업별 공시 수치가 들어 있고, API 키는 어디에도 넣지 않음
- 근거 분석(f5, f8~f12)의 코드는 옛 계산 코드에 기대고 있어 넣지 않음, 결과 파일만 `3_결과/3_산술식/근거_*`에 있음
