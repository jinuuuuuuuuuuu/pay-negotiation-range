---
version: 1
slug: "index-html"
primary_target: "index.html"
related_targets: []
---

## Scope

`index.html` 단일 페이지 앱(해시 라우팅): 회사 찾기 → 요약·진단 → 인상안 협상 구간 → 이익연동 전환 → 미래 위험(업계 불황 대비 점검) → 근거와 한계. Visitor mode: **Operate** (휴대폰 375×812 기준, 360~430 폭).

Audience/job: 성과급·Base-up 요구를 받은 급여·노무 담당자가 회사 하나를 골라 협상 시작점을 정한다. 시연 청중(심사위원, 현업 선배)이 휴대폰 화면으로 기능을 이해한다.

Constraints: 계산은 js/engine.js(formula.py와 일치 테스트) 그대로. Figma iBank 키트는 레이아웃·크기 체계만 참고(라이선스 문구가 Hello 페이지에 없어 이미지·일러스트·아이콘은 쓰지 않음). 아이콘은 Lucide(ISC). 폰트 Pretendard. PPT 색.

Unresolved: 최종 PPT 색이 바뀌면 다시 맞춤. GitHub Pages 배포는 사용자 확인 후.

## Direction contract

THESIS: 이 화면은 "정답 숫자" 대신 **양측 근거의 구간**을 보여 준다. 협상 구간 그래프(x = 기본급 인상률, y = 영업이익 중 인상 비용; 하한 = 업계 인상률, 상한 = 우리 부담선이 업계 부담선과 만나는 곳) 위에 노조안·회사안이 점으로 찍힌다(11-22 사용자 피드백으로 막대에서 x·y 그래프로). 카테고리 기본값인 '큰 숫자 + 작은 라벨' 대시보드 카드 격자를 거부한다.

OWN-WORLD: 밝은 중성 회색 바탕(#F3F3F2, detector의 크림 바탕 경고로 #F6F5F1에서 조정)과 흰 면, PPT의 거의 검정(#1F1F1F) 요약 카드, 노랑(#FFCD4A 주행동·선택, #FFEFA8 구간 띠) 강조, 회색 #595959 보조 글자. 판정 색은 노랑과 겹치지 않게 하한 미달 파랑, 구간 안 초록, 상한 초과 주황빨강. Pretendard 한 가족, 숫자는 tabular. 둥근 모서리 16px, 그림자 offset y4 blur 30 투명도 7%(키트 규칙). 사용 장면: 사무실 낮 조명에서 협상을 준비하고 발표장에서 휴대폰으로 시연 → 밝은 바탕.

STORY: 담당자는 회사를 고르면 먼저 업계 대비 임금 위치와 이익 체력을 이해하고, 협상 구간에서 하한·상한이 각각 누구의 근거인지 믿게 되며, 노조안·회사안을 넣어 구간 위치·비용·내년 위치를 비교하고, 이익연동과 불황 시 결과로 대안을 확인한다.

FIRST VIEWPORT: 회사 화면 첫 화면은 상단 검은 요약 카드(회사명, 업종, 임금 위치·이익 체력 두 배지, 협상 구간 한 줄 "하한 5.6% ~ 상한 7.9%")가 화면 폭 전체, 그 아래 한 줄 진단(한 문장 + 핵심 3개), 협상 구간 그래프 미리보기, 하단 고정 탭(요약 / 협상 구간 / 이익연동 / 미래 위험). 주행동 "협상 구간 보기"는 막대 아래 노란 버튼. 회사 찾기 첫 화면은 검색창이 화면 위쪽 1/3, 예시 회사 칩.

FORM: 모바일 업무 앱(키트의 홈·폼·목록 패턴), 순위 1/1. seed: none (pinned) — "주요 디자인은 [iBank Figma 키트]에서, 메인 색상은 우리가 만든 PPT에서 가져와서 적용"

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
