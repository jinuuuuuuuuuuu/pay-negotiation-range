---
name: 인상안 협상 구간
description: 급여·노무 담당자가 성과급·임금 요구를 받았을 때 업계 비교군 20곳 기준의 협상 구간과 근거를 휴대폰에서 확인하는 업무 앱
colors:
  band-yellow: "#FFCD4A"
  band-yellow-hi: "#FFE15B"
  band-yellow-soft: "#FFEFA8"
  table-black: "#1F1F1F"
  graphite: "#595959"
  graphite-light: "#6E6E6E"
  page-gray: "#F3F3F2"
  card-white: "#FFFFFF"
  card-tint: "#FAFAF9"
  rule-gray: "#E5E5E3"
  rule-gray-strong: "#D3D3D0"
  hold-gray-soft: "#ECECEA"
  below-blue: "#2560C8"
  below-blue-soft: "#E6EEFB"
  inside-green: "#1E7A4E"
  inside-green-soft: "#E3F3EA"
  above-red: "#C23B22"
  above-red-soft: "#FBE8E3"
  on-dark-muted: "#CFCCC4"
  bar-gray: "#CFCFCB"
  bar-gray-deep: "#B5B5B1"
typography:
  display:
    fontFamily: "Pretendard Variable, Pretendard, -apple-system, Apple SD Gothic Neo, Malgun Gothic, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  figure:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "34px"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.03em"
    fontFeature: "tnum"
  title-lg:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "18px"
    fontWeight: 650
    lineHeight: 1.35
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "17px"
    fontWeight: 650
    lineHeight: 1.4
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "-0.01em"
  body-lg:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.5
  body-sm:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.55
  caption:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.5
  chart-label:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.2
    fontFeature: "tnum"
  label:
    fontFamily: "Pretendard Variable, Pretendard, sans-serif"
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.3
    fontFeature: "tnum"
rounded:
  pill: "999px"
  hero: "28px"
  card: "16px"
  button: "14px"
  control: "12px"
  segment: "9px"
  tag: "8px"
  bar: "6px"
  mark: "4px"
  hairline: "3px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  gutter: "20px"
  section: "28px"
components:
  button-primary:
    backgroundColor: "{colors.band-yellow}"
    textColor: "{colors.table-black}"
    rounded: "{rounded.control}"
    height: "52px"
    padding: "0 20px"
  button-primary-hover:
    backgroundColor: "{colors.band-yellow-hi}"
  button-secondary:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.table-black}"
    rounded: "{rounded.control}"
    height: "52px"
  chip:
    backgroundColor: "{colors.card-white}"
    textColor: "{colors.table-black}"
    rounded: "{rounded.pill}"
    height: "36px"
    padding: "0 14px"
  chip-hover:
    backgroundColor: "{colors.band-yellow-soft}"
  card:
    backgroundColor: "{colors.card-white}"
    rounded: "{rounded.card}"
    padding: "18px"
  summary-card:
    backgroundColor: "{colors.table-black}"
    textColor: "{colors.card-white}"
    rounded: "{rounded.hero}"
  stepper:
    backgroundColor: "{colors.card-tint}"
    textColor: "{colors.table-black}"
    rounded: "{rounded.control}"
    height: "48px"
  tab-active:
    backgroundColor: "{colors.table-black}"
    textColor: "{colors.card-white}"
    rounded: "14px"
  badge-inside:
    backgroundColor: "{colors.inside-green-soft}"
    textColor: "{colors.inside-green}"
    rounded: "{rounded.tag}"
    height: "28px"
  badge-below:
    backgroundColor: "{colors.below-blue-soft}"
    textColor: "{colors.below-blue}"
    rounded: "{rounded.tag}"
    height: "28px"
  badge-above:
    backgroundColor: "{colors.above-red-soft}"
    textColor: "{colors.above-red}"
    rounded: "{rounded.tag}"
    height: "28px"
---

# Design System: 인상안 협상 구간

<!-- 2026-11-22 예약 작업에서 완성된 화면(css/app.css)을 기준으로 작성. 사용자가 자는 중이라 콘셉트 이름·색 이름 같은 표현은 작성자가 정했고 사용자 확인이 필요하다. -->

## Overview

**Creative North Star: "협상 테이블 위의 노란 띠"** *(작성자 제안, 확인 필요)*

이 시스템은 팀 발표 자료의 두 색, 거의 검정에 가까운 먹색과 노랑으로 업무 앱을 짓는다. 먹색은 "지금 우리 회사의 상태"를 담는 요약 카드와 선택된 탭에만 쓰고, 노랑은 협상 구간의 띠와 그 화면으로 가는 주행동에만 쓴다. 나머지는 중성 회색 바탕과 흰 카드가 맡아, 숫자가 가장 먼저 읽히게 한다.

밀도는 휴대폰 업무 앱 수준이다. 한 화면에 한 가지 질문(지금 어디인가, 구간은 어디인가, 연동이면 어떤가, 불황이면 어떤가)을 두고, 카드 하나에 답 하나를 담는다. 장식은 없고, 움직임은 협상 구간의 점이 새 값으로 미끄러지는 한 가지뿐이다.

레이아웃과 크기 체계는 iBank 모바일 뱅킹 키트(Figma 커뮤니티)의 패턴을 참고했다. 키트의 이미지·일러스트·아이콘은 쓰지 않았다(라이선스 문구가 파일에 없어서). 아이콘은 Lucide(ISC)다.

**Key Characteristics:**
- 먹색 요약 카드 + 노란 협상 구간 줄이 회사 화면의 첫인상
- 협상 구간 그래프(x = 기본급 인상률, y = 영업이익 중 인상 비용): 우리 회사 부담선(먹색 실선)이 업계 부담선(점선)과 만나는 곳이 상한, 하한~상한은 연한 노랑 면
- 그래프는 통계식 표현(점 분포, 범위 막대) 대신 막대·선처럼 바로 읽히는 모양만 쓴다 (11-22 사용자 피드백)
- 중성 회색 바탕(#F3F3F2) 위의 흰 카드, 부드러운 그림자
- Pretendard 한 가족, 숫자는 고정폭 숫자
- 판정 색 세 가지(파랑·초록·주황빨강)는 노랑과 겹치지 않음

## Colors

먹색과 노랑 두 목소리에 중성 회색을 깔고, 판정에만 의미 색을 쓰는 절제형 팔레트.

### Primary
- **구간 노랑** (band-yellow): 협상 구간의 띠, 주행동 버튼, 협상 구간 요약 줄의 바탕, 선택된 탭의 아이콘. 글자색으로는 쓰지 않는다.
- **밝은 노랑** (band-yellow-hi): 주행동 버튼의 hover.
- **연한 노랑** (band-yellow-soft): 해석 문장 상자, 검색어 강조, 칩 hover, 텍스트 선택.

### Secondary
- **테이블 먹색** (table-black): 회사 요약 카드, 상단바(요약 화면), 선택된 탭, 본문 글자, 막대 눈금과 노조안 점, 포커스 링.

### Tertiary
- **아래 파랑** (below-blue / below-blue-soft): "하한 미달", "상한 이하".
- **안 초록** (inside-green / inside-green-soft): "구간 안", "흑자 유지".
- **위 주황빨강** (above-red / above-red-soft): "상한 초과", "지급 때문에 적자", 음수 영업이익, 업계보다 부담이 커지는 구간.

### Neutral
- **흑연** (graphite): 보조 글자, 설명 문장. 흰 바탕 대비 7:1.
- **옅은 흑연** (graphite-light): 축 눈금, 비활성 탭 글자. 흰 바탕 대비 4.5:1 이상.
- **페이지 회색** (page-gray): 앱 바탕.
- **카드 흰색 / 카드 틴트** (card-white / card-tint): 카드, 입력 칸 바탕.
- **구분선 회색** (rule-gray / rule-gray-strong): 표 줄, 칩 테두리, 입력 칸 테두리.
- **보류 회색** (hold-gray-soft): 막대 트랙, 분절 버튼 바탕, 보류·비교 불가 배지.
- **먹색 위 보조 글자** (on-dark-muted): 요약 카드 안의 설명.

### Named Rules
**The 노랑은 면이다 Rule.** 노랑은 띠, 버튼, 상자의 면으로만 쓴다. 흰 바탕의 노란 글자는 금지(대비 부족). 노랑 위의 글자는 먹색.

**The 판정 색은 판정에만 Rule.** 파랑·초록·주황빨강은 구간 위치와 적자 여부 판정에만 쓴다. 장식이나 강조에 빌려 쓰지 않는다.

## Typography

**Display Font:** Pretendard Variable (Apple SD Gothic Neo, Malgun Gothic 대체)
**Body Font:** 같은 가족

**Character:** 한국어 업무 문서에 맞는 단정한 산세리프 한 가족. 굵기와 크기 차이만으로 위계를 만든다.

### Hierarchy
- **Display** (700, 26px, 1.25): 회사명(요약 카드), 회사 찾기 제목.
- **Headline** (700, 20px, 1.3): 협상 구간 요약 줄의 숫자.
- **Title** (650, 17px, 1.4): 섹션 제목, 상단바 제목(18px).
- **Body** (400, 15px, 1.55): 설명, 진단 문장(15px, 1.7). 설명 문단은 68ch 이내.
- **Figure** (700, 34px): 다음 해 적자 확률 같은 화면의 대표 숫자 하나.
- **Body-lg / Body-sm / Caption** (16px 600 / 14px / 13px): 한 줄 진단 문장 / 표·설명 / 보조 설명.
- **Label** (600, 12px, 고정폭 숫자): 입력 칸 라벨, 탭 이름. 그래프 안 글자는 11px(chart-label).

### Named Rules
**The 숫자는 줄을 맞춘다 Rule.** 금액·비율이 나오는 표와 칸은 모두 고정폭 숫자(tabular-nums). 음수는 하이픈이 아니라 마이너스 기호(−).

## Layout

휴대폰 한 열 레이아웃. 앱 폭은 최대 480px이고, 그보다 넓은 화면에서는 가운데 정렬한 휴대폰 틀로 보인다. 좌우 여백은 20px(gutter), 섹션 간격은 28px, 카드 안 여백은 18px, 카드끼리는 12px. 상단바는 56px(+안전 영역)로 위에 고정, 회사 화면에서는 64px 하단 탭이 아래에 고정되고 본문은 그만큼 아래 여백을 둔다. 입력은 두 칸 격자(1fr 1fr)로 나란히 놓는다. 360~430px 폭에서 확인했다.

## Elevation & Depth

부드러운 그림자 한 단계와 면의 대비로 깊이를 낸다. 카드는 바탕보다 밝은 흰색에 넓게 퍼지는 옅은 그림자를 둔다.

### Shadow Vocabulary
- **카드 그림자** (`box-shadow: 0 4px 30px rgba(31,31,31,0.07)`): 모든 카드, 검색 칸, 입력 묶음. Figma 키트의 카드 그림자 규칙(blur 30, y 4, 7%)을 먹색으로 옮긴 것.
- **작은 그림자** (`box-shadow: 0 2px 12px rgba(31,31,31,0.06)`): 분절 버튼의 선택된 칸, 스위치 손잡이.

### Named Rules
**The 그림자 한 겹 Rule.** 카드 안에 그림자 있는 카드를 다시 넣지 않는다. 카드 안의 구분은 선(구분선 회색)이나 틴트로 한다.

## Shapes

둥근 사각형 언어. 카드 16px, 입력·버튼 12~14px, 배지 8px, 칩과 막대 트랙은 완전한 알약형. 회사 요약 카드는 아래쪽 두 모서리만 28px로 둥글려 상단바와 이어진 한 덩어리로 보이게 한다. 한쪽에만 선을 긋는 장식(side stripe)은 쓰지 않는다.

## Components

### Buttons
- **Shape:** 둥근 모서리(14px), 높이 52px, 폭 가득
- **Primary:** 구간 노랑 바탕 + 먹색 글자(16px, 650). 협상 구간으로 가는 주행동에만
- **Hover / Focus:** 밝은 노랑으로 0.18s 전환, 누르면 1px 아래로. 포커스는 먹색 3px 링
- **Secondary:** 흰 바탕 + 구분선 회색 1.5px 안쪽 테두리. 두 개를 나란히 놓을 때는 15px, 줄바꿈 금지

### Chips
- **Style:** 흰 바탕, 구분선 회색 1px 안쪽 테두리, 알약형, 높이 36px
- **State:** hover 시 연한 노랑 바탕 + 노랑 테두리. 예시 회사, "시작값으로" 같은 빠른 입력에 사용

### Cards / Containers
- **Corner Style:** 16px
- **Background:** 카드 흰색
- **Shadow Strategy:** 카드 그림자 한 겹
- **Internal Padding:** 18px (입력 묶음은 16px)
- **펼침 카드:** 같은 카드 모양에 제목 줄과 오른쪽 화살표(펼치면 90도 회전)

### Inputs / Fields
- **Style:** 스테퍼(− 값 % +), 높이 48px, 카드 틴트 바탕, 구분선 1.5px 안쪽 테두리, 12px 모서리. 값은 17px 650 고정폭 숫자
- **Focus:** 테두리가 먹색 2px로 바뀜
- **검색 칸:** 높이 56px, 흰 바탕, 카드 그림자, 왼쪽 돋보기 아이콘
- **스위치:** 50×30px, 켜면 먹색

### Navigation
- **상단바:** 뒤로(44px 터치 영역) · 제목 · 근거 보기(i). 요약 화면에서는 먹색으로 바뀌어 요약 카드와 이어짐
- **하단 탭:** 요약 / 협상 구간 / 이익연동 / 미래 위험. 선택된 탭은 먹색 알약 + 노랑 아이콘 + 흰 글자, 나머지는 옅은 흑연

### 협상 구간 그래프 (Signature)
가로축은 기본급 인상률, 세로축은 영업이익 중 인상 비용(기본급 인상분, 3년 평균 이익 기준). 우리 회사 부담은 원점에서 오르는 먹색 실선(2.5px), 업계 부담(비교군이 업계 인상률만큼 올릴 때)은 흑연 점선 수평선. 하한(업계 인상률)은 먹색 세로 실선, 상한은 세로 점선이고, 두 선이 만나는 곳에 노란 점을 찍는다. 하한~상한은 연한 노랑 면, 상한이 하한보다 낮으면 그 사이를 위 주황빨강 연한 면으로 칠한다. 노조안은 채운 먹색 점, 회사안은 빈 점으로 우리 회사 선 위에 놓고, 입력할 때마다 즉시 다시 그린다. 선 이름은 그래프 안이 아니라 아래 범례에 둔다(글자 겹침 방지). 상한이 10%를 넘으면 "상한 10% 초과", 비교군 적자로 보류면 하한선만, 우리 회사가 3년 적자면 우리 회사 선 없이 표시한다.

### 업계 대비 임금 위치 막대그래프
비교군 20곳과 우리 회사의 1인당 급여(3년)를 높은 순으로 세운 세로 막대. 다른 회사는 막대 회색, 우리 회사는 구간 노랑 + 먹색 테두리와 금액 이름표. 업계 중앙값은 점선 수평선. 아래에 "21곳 중 n위".

### 시나리오 막대 (미래 위험)
0을 가운데 둔 가로 막대. 양수는 먹색, 음수는 위 주황빨강, 0에 흑연 기준선. 모델 예측은 최악·보통·최적의 시나리오 세 줄, 업계 불황 대비 점검은 "불황이 없을 때 / 이 불황이 오면" 두 줄로 쓴다.

### 불황 고르기
업계 불황 대비 점검은 시나리오를 한꺼번에 나열하지 않고, 기본 select(52px, 14px 모서리, 왼쪽 아이콘)로 하나를 고르면 그 하나만 자세히 보여 준다: 이름, 종류·근거, 무슨 일이 있었는지, 충격 크기(위 주황빨강 연한 상자), 출처 링크, 두 줄 막대, 비교 표.

### 판정 배지
높이 28px, 8px 모서리, 판정 색의 연한 면 + 진한 글자 + 같은 색 점. 표 칸에서는 줄바꿈을 허용한다.

## Do's and Don'ts

### Do:
- **Do** 협상 구간은 언제나 하한(노측 근거)과 상한(사측 근거)을 같은 그래프 위에 함께 그린다.
- **Do** 그래프는 막대와 선처럼 설명 없이 읽히는 모양으로, 화면 문구는 "업계"로 통일한다(업종 금지).
- **Do** 구간 노랑(#FFCD4A)은 띠·주행동·요약 줄의 면에만, 위 글자는 먹색으로 쓴다.
- **Do** 숫자 칸은 고정폭 숫자와 마이너스 기호(−)를 쓴다.
- **Do** 보류·비교 불가·예측 대상 아님 같은 상태는 숨기지 말고 보류 회색 상자로 이유와 함께 보여 준다.
- **Do** 터치 영역은 44px 이상, 포커스는 먹색 3px 링.

### Don't:
- **Don't** 흰 바탕에 노란 글자를 쓰지 않는다.
- **Don't** 판정 색(파랑·초록·주황빨강)을 장식이나 강조에 쓰지 않는다.
- **Don't** 카드 안에 그림자 있는 카드를 넣지 않는다(카드 안 구분은 선이나 틴트).
- **Don't** 크림·베이지 바탕으로 돌아가지 않는다(페이지 회색 #F3F3F2 유지).
- **Don't** 키트의 이미지·일러스트·아이콘을 가져오지 않는다.
- **Don't** 점 분포(strip plot), 범위 막대(fan) 같은 통계식 시각화를 쓰지 않는다.
