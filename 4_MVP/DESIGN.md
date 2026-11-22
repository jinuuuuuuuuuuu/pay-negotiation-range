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
  below-graphite: "#3D3D3D"
  below-graphite-soft: "#E6E6E4"
  inside-yellow: "#1F1F1F"
  inside-yellow-soft: "#FFE38F"
  above-orange: "#A3440B"
  above-orange-soft: "#FFE3CC"
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
  hero: "30px"
  card: "24px"
  field: "16px"
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
    backgroundColor: "{colors.inside-yellow-soft}"
    textColor: "{colors.inside-yellow}"
    rounded: "{rounded.tag}"
    height: "28px"
  badge-below:
    backgroundColor: "{colors.below-graphite-soft}"
    textColor: "{colors.below-graphite}"
    rounded: "{rounded.tag}"
    height: "28px"
  badge-above:
    backgroundColor: "{colors.above-orange-soft}"
    textColor: "{colors.above-orange}"
    rounded: "{rounded.tag}"
    height: "28px"
---

# Design System: 인상안 협상 구간

<!-- 2026-11-22 예약 작업에서 완성된 화면(css/app.css)을 기준으로 작성. 사용자가 자는 중이라 콘셉트 이름·색 이름 같은 표현은 작성자가 정했고 사용자 확인이 필요하다. -->

## Overview

**Creative North Star: "협상 테이블 위의 노란 띠"** *(작성자 제안, 확인 필요)*

이 시스템은 팀 발표 자료의 두 색, 거의 검정에 가까운 먹색과 노랑으로 업무 앱을 짓는다. 먹색은 "지금 우리 회사의 상태"를 담는 요약 카드와 선택된 탭에만 쓰고, 노랑은 협상 구간의 띠와 그 화면으로 가는 주행동에만 쓴다. 나머지는 중성 회색 바탕과 흰 카드가 맡아, 숫자가 가장 먼저 읽히게 한다.

밀도는 휴대폰 업무 앱 수준이다. 한 화면에 한 가지 질문(지금 어디인가, 구간은 어디인가, 연동이면 어떤가, 불황이면 어떤가)을 두고, 카드 하나에 답 하나를 담는다. 장식은 없다. 움직임은 의미가 있는 곳에만 둔다. **대표 움직임:** 임금 그래프가 화면에 들어오면 막대가 바닥에서 왼쪽부터 차례로 자라고(460ms, 막대 사이 지연 합계 최대 440ms), 우리 막대가 다 자라는 순간 노랑 띠와 먹색 배지가 나타난다. 같은 때 큰 숫자가 0부터 올라간다(700ms). **곁들임:** 요약 화면에 들어오면 노란 협상 구간 카드가 시트 경계로 16px 올라와 자리 잡고(450ms, 40% 지점에서 불투명), 툴팁은 150ms 떠오르며, 입력에 따른 변화는 다시 그리지 않고 바뀐 곳만 고친다(morph): 그래프 좌표(점·띠·선·이름표)는 300ms 동안 새 값으로 미끄러지고, 바뀐 숫자 칸은 750ms 동안 연한 노랑으로 빛나며(슬라이더를 끄는 동안은 450ms에 한 번), 판정 배지가 바뀌면 320ms 톡 튄다. 모양이 달라져 통째로 다시 그릴 때는 300ms 떠오름. **화면 전환:** 섹션이 14px 아래에서 차례로 떠오르고(420ms, 지연 합계 최대 240ms, 헤더·걸친 카드 제외), 선택된 탭은 먹색 알약으로 차오른다(320ms). **첫 등장(한 번만):** 협상 구간 그래프는 노랑 띠가 하한에서 상한으로 펼쳐지고(600ms) 우리 부담선이 그려진 뒤(800ms) 노조안·회사안 점이 나타난다. 미래 위험은 확률 숫자가 0부터 올라가고 막대가 0 기준선에서 자라며, 불황 충격 표시와 판정 배지가 나타난다. **누름:** 버튼 0.98배, 칩·탭·스테퍼·구분 버튼 0.94배. 펼침 메뉴는 내용이 280ms 떠오른다. 곡선은 모두 cubic-bezier(0.16, 1, 0.3, 1). 기본 상태는 끝 상태(스크립트 실패·인쇄 때도 그래프가 보임), 동작 줄이기 설정에서는 이동 없이 카드만 200ms 흐려짐으로 나타난다.

레이아웃과 크기 체계는 iBank 모바일 뱅킹 키트(Figma 커뮤니티)의 패턴을 참고했다. 키트의 이미지·일러스트·아이콘은 쓰지 않았다(라이선스 문구가 파일에 없어서). 아이콘은 Lucide(ISC)다.

**Key Characteristics:**
- 먹색 요약 카드 + 노란 협상 구간 줄이 회사 화면의 첫인상
- 협상 구간 그래프(x = 기본급 인상률, y = 영업이익 중 인상 비용): 우리 회사 부담선(먹색 실선)이 업계 부담선(점선)과 만나는 곳이 상한, 하한~상한은 연한 노랑 면
- 그래프는 통계식 표현(점 분포, 범위 막대) 대신 막대·선처럼 바로 읽히는 모양만 쓴다 (11-22 사용자 피드백)
- 중성 회색 바탕(#F3F3F2) 위의 흰 카드, 부드러운 그림자
- Pretendard 한 가족, 숫자는 고정폭 숫자
- 판정 색 세 가지(진회색·노랑·주황)는 노랑과 겹치지 않음

## Colors

먹색과 노랑 두 목소리에 중성 회색을 깔고, 판정에만 의미 색을 쓰는 절제형 팔레트.

### Primary
- **구간 노랑** (band-yellow): 협상 구간의 띠, 주행동 버튼, 협상 구간 요약 줄의 바탕, 선택된 탭의 아이콘. 글자색으로는 쓰지 않는다.
- **밝은 노랑** (band-yellow-hi): 주행동 버튼의 hover.
- **연한 노랑** (band-yellow-soft): 해석 문장 상자, 검색어 강조, 칩 hover, 텍스트 선택.

### Secondary
- **테이블 먹색** (table-black): 회사 요약 카드, 상단바(요약 화면), 선택된 탭, 본문 글자, 막대 눈금과 노조안 점, 포커스 링.

### Tertiary
- **아래 파랑** (below-graphite / below-graphite-soft): "하한 미달", "상한 이하".
- **안 초록** (inside-yellow / inside-yellow-soft): "구간 안", "흑자 유지".
- **위 주황빨강** (above-orange / above-orange-soft): "상한 초과", "지급 때문에 적자", 음수 영업이익, 업계보다 부담이 커지는 구간.

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

**The 판정 색은 판정에만 Rule.** 진회색·노랑·주황은 구간 위치와 적자 여부 판정에만 쓴다. 장식이나 강조에 빌려 쓰지 않는다.

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

휴대폰 한 열 레이아웃. 앱 폭은 최대 480px이고, 그보다 넓은 화면에서는 가운데 정렬한 휴대폰 틀로 보인다. 좌우 여백은 20px(gutter), 섹션 간격은 28px, 카드 안 여백은 20px, 카드끼리는 12px. 상단바는 56px(+안전 영역)로 위에 고정, 회사 화면에서는 64px 하단 탭이 아래에 고정되고 본문은 그만큼 아래 여백을 둔다. 입력은 두 칸 격자(1fr 1fr)로 나란히 놓는다. 360~430px 폭에서 확인했다.

## Elevation & Depth

부드러운 그림자 한 단계와 면의 대비로 깊이를 낸다. 카드는 바탕보다 밝은 흰색에 넓게 퍼지는 옅은 그림자를 둔다.

### Shadow Vocabulary
- **카드 그림자** (`box-shadow: 0 4px 30px rgba(31,31,31,0.07)`): 모든 카드, 검색 칸, 입력 묶음. Figma 키트의 카드 그림자 규칙(blur 30, y 4, 7%)을 먹색으로 옮긴 것.
- **작은 그림자** (`box-shadow: 0 2px 12px rgba(31,31,31,0.06)`): 분절 버튼의 선택된 칸, 스위치 손잡이.

### Named Rules
**The 그림자 한 겹 Rule.** 카드 안에 그림자 있는 카드를 다시 넣지 않는다. 카드 안의 구분은 선(구분선 회색)이나 틴트로 한다.

## Shapes

둥근 사각형 언어(Figma iBank 키트 기준). 카드 24px(키트 30px과 참고 이미지 사이), 입력·버튼 12~14px, 배지 8px, 칩과 막대 트랙은 완전한 알약형. **헤더와 시트:** 요약 화면은 먹색 헤더 아래로 바탕색 시트가 위 두 모서리 30px로 올라오고, 노란 협상 구간 카드가 헤더와 시트 경계에 걸친다(키트 Transaction report의 카드 배치). 헤더 안 지표 두 개는 반투명 패널 하나에 세로선으로 나눈다. 한쪽에만 선을 긋는 장식(side stripe)은 쓰지 않는다.

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
비교군 20곳과 우리 회사의 1인당 급여(3년)를 **낮은 순 → 높은 순**(왼쪽 → 오른쪽)으로 세운 세로 막대. 세로축 눈금 없이 맨 왼쪽·맨 오른쪽 막대 아래에 최솟값·최댓값만 적고(우리 막대가 끝이면 그쪽은 생략), 축 아래 가운데에 "← 급여 낮음 · 높음 →" 한 줄.
- **판정 구간 음영:** 왼쪽 6칸 "하위 25%", 오른쪽 6칸 "상위 25%"를 페이지 회색(#F3F3F2) 면으로. 오름차순 i번째 칸의 P = i ÷ 비교 회사 수라서, 이 칸이 formula.py의 임금 낮음(P ≤ 0.25)·임금 높음(P ≥ 0.75) 자리와 같다. 판정 색은 쓰지 않는다.
- **우리 막대:** 구간 노랑 + 먹색 2px 테두리(흑백 인쇄·프로젝터 대비), 이름표는 "우리 n만" 하나. 중앙선 이름표와 겹치면 한 줄 위로.
- **업계 중앙:** 흑연 점선 수평선, 이름표는 왼쪽 위(오른쪽 높은 막대와 겹치지 않게). 이름표는 흰 테두리 글자(halo)로 막대 위에서도 읽히게.
- **머리:** 결론 문장("업계 중앙보다 n만 원 높음/낮음", 20px 700)을 가장 크게, 아래 줄에 먹색 순위 배지("21곳 중 n위") + "상위/하위 n% · 판정". 숫자 표(우리·중앙·대비·순위)는 두지 않는다. 비교군 주의(매출 규모 차이)는 해당될 때만 제목 옆 ⓘ 버튼 → 누르면 회색 상자로 이유.
- **키트 막대 모양:** 막대는 폭 5~9px의 끝이 둥근 기둥, 우리 칸은 연한 노랑 세로 띠로 강조하고 우리 막대 위에 먹색 알약 이름표("우리 n만"). 머리는 작은 회색 라벨("업계 중앙보다") + 큰 숫자(figure 34px) + 작은 단위("만 원 높음"), ⓘ는 머리 오른쪽 위.
- **탭·호버:** 막대 칸 전체(세로 전부)가 누름 영역. 누르거나 마우스를 올리면 먹색 말풍선에 회사명·급여·순위, 선택한 막대는 흑연으로. 그래프에 초점이 있으면 ←/→로 옮기고 Esc로 닫는다. "비교군 보기" 목록에도 우리 회사 행을 넣어 연한 노랑 면으로 강조.

### 목록 행 (키트 Row)
왼쪽 40px 칩(12px 모서리, 회색 면) + 제목(15px 600)·보조(12px 흑연) + 오른쪽 값(15px 650), 행 사이 1px 선. 비교군 목록은 칩에 순위 번호, 회사 검색 결과는 회사 이름 첫 글자. 우리 회사 행은 연한 노랑 면 + 노랑 칩·먹색 테두리.

### 색 통일: 검정 · 회색 · 흰색 · 노랑 · 주황 (2026-11-22 사용자 결정)
앱 전체의 색은 이 다섯 계열 안에서만 쓴다. 파랑·초록·빨강·보라·청록은 쓰지 않는다.
- **판정 색도 이 안으로:** 하한 미달 = 진회색(#3D3D3D, 면 #E6E6E4), 구간 안·흑자 유지 = 노랑 면(#FFE38F) + 먹색, 상한 초과·적자 = 주황(글자 #A3440B, 면 #FFE3CC, 막대 #FF8A3D)
- **면 4색:** 버터(#FFF1C2 / 글자 #6E4E00), 살구 주황(#FFE3CC / #A3440B), 회색(#ECECEA / #3D3D3D), 호박(#FFE6A8 / #7A4A00). 막대는 노랑 #FFCD4A, 주황 #FF8A3D, 회색 #9A9A96
- **협상 구간 눈금자 칸:** 업계보다 뒤처짐 #DCDCD9 · 협상 구간 #FFCD4A · 업계보다 부담 큼 #FFB07A
- **역할:** 노조안 = 노랑, 회사안 = 주황 / 고정·평상시 = 회색, 연동 = 노랑, 불황 = 주황

### 대결형 막대 비교 (두 안 비교 · 고정 vs 연동 · 평상시 vs 불황)
맨 위에 두 쪽 머리(색 면 카드, VS)를 마주 세우고, 줄마다 [A 값 + 왼쪽으로 자라는 막대 | 가운데 항목 + 차이 칩 | B 값 + 오른쪽으로 자라는 막대]. 막대는 그 줄의 큰 값 기준. 차이 칩은 먹색 알약에 차이 크기와 큰 쪽을 가리키는 노랑 화살표. 두 값이 모두 없는 줄은 뺀다.

### 비어 있는 값
"자료 부족", "—", "비교 불가", "계산할 수 없음"은 보여 주지 않는다. 값이 없는 칸·줄·섹션은 숨기고, 비교군이 없는 회사의 협상 구간은 "업계 인상률 넣고 계산" 버튼으로 바꾼다.
### 문장 대신 쓰는 정리 부품
- **소제목 아이콘 칩:** 28px 칩(9px 모서리, 파스텔 면 + 진한 아이콘) + 제목
- **핵심 태그:** 소제목 아래 설명 문장 대신 알약 태그 2~4개(12.5px 600, 파스텔 4색이 돌아감)
- **지표 타일:** 문장 속 숫자를 꺼낸 16px 모서리 파스텔 타일(항목 12px · 값 18px 700 · 보조 12px)
- **정리 목록:** 문단 대신 "항목 | 내용 + 회색 보조" 두 칸 목록
- **좌우 비교:** 표 대신 줄마다 [항목 | A 칸 | B 칸]. 칸은 파스텔 면 + 오른쪽 정렬 값 + 그 줄의 큰 값 기준 미니 막대(4px). 적자 금액만 빨강. 판정은 배지.
- **경고 줄:** 회색 면 + 알림 아이콘 한 줄

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
- **Don't** 판정 색(진회색·노랑·주황)을 장식이나 강조에 쓰지 않는다.
- **Don't** 카드 안에 그림자 있는 카드를 넣지 않는다(카드 안 구분은 선이나 틴트).
- **Don't** 크림·베이지 바탕으로 돌아가지 않는다(페이지 회색 #F3F3F2 유지).
- **Don't** 키트의 이미지·일러스트·아이콘을 가져오지 않는다.
- **Don't** 점 분포(strip plot), 범위 막대(fan) 같은 통계식 시각화를 쓰지 않는다.
