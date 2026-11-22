"""impeccable 사이드카 .impeccable/design.json 생성 (DESIGN.md의 토큰을 보충: 색 단계, 그림자, 움직임, 컴포넌트 예시).
DESIGN.md를 고치면 이 파일도 다시 돌린다:  python scripts/make_design_json.py   (4_MVP 폴더에서)"""
import colorsys
import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = "'Pretendard Variable',Pretendard,sans-serif"


def hex2rgb(h):
    h = h.lstrip('#')
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def rgb2hex(r):
    return '#%02X%02X%02X' % tuple(max(0, min(255, round(v * 255))) for v in r)


def ramp(h):
    r, g, b = hex2rgb(h)
    hh, _, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    for L in [0.15, 0.27, 0.39, 0.51, 0.63, 0.75, 0.86, 0.95]:
        ss = s * (1 - abs(L - 0.5) * 1.2) if s > 0 else 0
        out.append(rgb2hex(colorsys.hls_to_rgb(hh, L, max(0, ss))))
    return out


COLORS = {
    'band-yellow': ('primary', '구간 노랑', '#FFCD4A'), 'table-black': ('secondary', '테이블 먹색', '#1F1F1F'),
    'below-blue': ('tertiary', '아래 파랑', '#2560C8'), 'inside-green': ('tertiary', '안 초록', '#1E7A4E'),
    'above-red': ('tertiary', '위 주황빨강', '#C23B22'), 'graphite': ('neutral', '흑연', '#595959'),
    'page-gray': ('neutral', '페이지 회색', '#F3F3F2'), 'rule-gray': ('neutral', '구분선 회색', '#E5E5E3'),
}

COMPONENTS = [
    dict(name='Primary Button', kind='button', refersTo='button-primary', description='협상 구간으로 가는 주행동',
         html='<button class="ds-btn-primary">노조안·회사안 넣어 보기</button>',
         css=f".ds-btn-primary{{background:#FFCD4A;color:#1F1F1F;height:52px;padding:0 20px;border:0;border-radius:14px;font:650 16px/1 {FONT};transition:background-color .18s cubic-bezier(.16,1,.3,1),transform .18s}}"
             ".ds-btn-primary:hover{background:#FFE15B}.ds-btn-primary:active{transform:translateY(1px)}.ds-btn-primary:focus-visible{outline:3px solid #1F1F1F;outline-offset:2px}"),
    dict(name='Secondary Button', kind='button', refersTo='button-secondary', description='다른 기능으로 가는 보조 행동',
         html='<button class="ds-btn-secondary">불황이 오면</button>',
         css=f".ds-btn-secondary{{background:#fff;color:#1F1F1F;height:52px;padding:0 16px;border:0;border-radius:14px;box-shadow:inset 0 0 0 1.5px #D3D3D0;font:650 15px/1 {FONT}}}"
             ".ds-btn-secondary:hover{background:#FAFAF9}.ds-btn-secondary:focus-visible{outline:3px solid #1F1F1F;outline-offset:2px}"),
    dict(name='Chip', kind='chip', refersTo='chip', description='예시 회사, 빠른 입력',
         html='<button class="ds-chip">현대자동차</button>',
         css=f".ds-chip{{background:#fff;color:#1F1F1F;height:36px;padding:0 14px;border:0;border-radius:999px;box-shadow:inset 0 0 0 1px #D3D3D0;font:550 14px/1 {FONT}}}"
             ".ds-chip:hover{background:#FFEFA8;box-shadow:inset 0 0 0 1px #FFCD4A}.ds-chip:focus-visible{outline:3px solid #1F1F1F;outline-offset:2px}"),
    dict(name='Stepper Input', kind='input', refersTo='stepper', description='인상률·성과급 % 입력',
         html='<div class="ds-step"><button>−</button><span><input value="4.5"><em>%</em></span><button>+</button></div>',
         css=".ds-step{display:grid;grid-template-columns:40px 1fr 40px;align-items:center;height:48px;width:170px;border-radius:12px;background:#FAFAF9;box-shadow:inset 0 0 0 1.5px #E5E5E3}"
             ".ds-step:focus-within{box-shadow:inset 0 0 0 2px #1F1F1F}.ds-step button{height:100%;border:0;background:transparent;font-size:20px;color:#595959}"
             ".ds-step span{display:flex;align-items:baseline;justify-content:center;gap:2px}"
             f".ds-step input{{width:100%;border:0;background:transparent;text-align:right;font:650 17px/1 {FONT};font-variant-numeric:tabular-nums;outline:none}}"
             ".ds-step em{font-style:normal;font-size:14px;color:#595959}"),
    dict(name='Tab Bar', kind='nav', refersTo='tab-active', description='회사 화면 하단 고정 탭',
         html='<nav class="ds-tabs"><a class="on">요약</a><a>협상 구간</a><a>이익연동</a><a>미래 위험</a></nav>',
         css=".ds-tabs{display:grid;grid-template-columns:repeat(4,1fr);gap:4px;padding:8px 12px;background:#fff;border-top:1px solid #E5E5E3;width:360px}"
             f".ds-tabs a{{display:flex;align-items:center;justify-content:center;height:48px;border-radius:14px;font:550 12px/1 {FONT};color:#6E6E6E}}.ds-tabs a.on{{background:#1F1F1F;color:#fff}}"),
    dict(name='Range Bar', kind='custom', refersTo=None, description='협상 구간 막대: 하한~상한 노란 띠, 노조안(채운 점)·회사안(빈 점)',
         html='<div class="ds-rbar"><div class="t"><div class="b" style="left:46%;width:19%"></div><i style="left:46%"></i><i style="left:65%"></i><s class="c" style="left:37%"></s><s class="u" style="left:62%"></s></div></div>',
         css=".ds-rbar{width:320px;padding:30px 0}.ds-rbar .t{position:relative;height:14px;border-radius:999px;background:#ECECEA}"
             ".ds-rbar .b{position:absolute;top:0;bottom:0;border-radius:999px;background:#FFCD4A}"
             ".ds-rbar i{position:absolute;top:-6px;width:2px;height:26px;background:#1F1F1F;border-radius:2px}"
             ".ds-rbar s{position:absolute;top:0;width:14px;height:14px;margin-left:-7px;border-radius:50%;box-shadow:0 0 0 3px #1F1F1F;background:#fff}.ds-rbar s.u{background:#1F1F1F}"),
    dict(name='Verdict Badge', kind='chip', refersTo='badge-inside', description='구간 위치 판정',
         html='<span class="ds-badge in">구간 안</span> <span class="ds-badge lo">하한 미달</span> <span class="ds-badge hi">상한 초과</span>',
         css=f".ds-badge{{display:inline-flex;align-items:center;height:28px;padding:0 10px;border-radius:8px;font:600 13px/1 {FONT}}}"
             ".ds-badge.in{background:#E3F3EA;color:#1E7A4E}.ds-badge.lo{background:#E6EEFB;color:#2560C8}.ds-badge.hi{background:#FBE8E3;color:#C23B22}"),
]

NARRATIVE = {
    'northStar': '협상 테이블 위의 노란 띠',
    'overview': '팀 발표 자료의 먹색과 노랑으로 짓는 업무 앱. 먹색은 지금 우리 회사의 상태를 담는 요약 카드와 선택된 탭에만, 노랑은 협상 구간의 띠와 그 화면으로 가는 주행동에만 쓴다. 나머지는 중성 회색 바탕과 흰 카드가 맡아 숫자가 먼저 읽히게 한다.',
    'keyCharacteristics': ['먹색 요약 카드 + 노란 협상 구간 줄', '협상 구간 그래프(우리 부담선이 업계 부담선과 만나는 곳이 상한, 하한~상한은 연한 노랑 면)', '중성 회색 바탕 위 흰 카드',
                           'Pretendard 한 가족, 고정폭 숫자', '판정 색 세 가지는 노랑과 겹치지 않음'],
    'rules': [
        {'name': 'The 노랑은 면이다 Rule', 'body': '노랑은 띠, 버튼, 상자의 면으로만 쓴다. 흰 바탕의 노란 글자는 금지(대비 부족). 노랑 위의 글자는 먹색.', 'section': 'colors'},
        {'name': 'The 판정 색은 판정에만 Rule', 'body': '파랑·초록·주황빨강은 구간 위치와 적자 여부 판정에만 쓴다. 장식이나 강조에 빌려 쓰지 않는다.', 'section': 'colors'},
        {'name': 'The 숫자는 줄을 맞춘다 Rule', 'body': '금액·비율이 나오는 표와 칸은 모두 고정폭 숫자(tabular-nums). 음수는 하이픈이 아니라 마이너스 기호(−).', 'section': 'typography'},
        {'name': 'The 그림자 한 겹 Rule', 'body': '카드 안에 그림자 있는 카드를 다시 넣지 않는다. 카드 안의 구분은 선(구분선 회색)이나 틴트로 한다.', 'section': 'elevation'},
    ],
    'dos': ['Do 협상 구간은 언제나 하한(노측 근거)과 상한(사측 근거)을 같은 그래프 위에 함께 그린다.',
            'Do 그래프는 막대와 선처럼 설명 없이 읽히는 모양으로, 화면 문구는 "업계"로 통일한다(업종 금지).',
            'Do 구간 노랑(#FFCD4A)은 띠·주행동·요약 줄의 면에만, 위 글자는 먹색으로 쓴다.',
            'Do 숫자 칸은 고정폭 숫자와 마이너스 기호(−)를 쓴다.',
            'Do 보류·비교 불가·예측 대상 아님 같은 상태는 숨기지 말고 보류 회색 상자로 이유와 함께 보여 준다.',
            'Do 터치 영역은 44px 이상, 포커스는 먹색 3px 링.'],
    'donts': ["Don't 흰 바탕에 노란 글자를 쓰지 않는다.",
              "Don't 판정 색(파랑·초록·주황빨강)을 장식이나 강조에 쓰지 않는다.",
              "Don't 카드 안에 그림자 있는 카드를 넣지 않는다(카드 안 구분은 선이나 틴트).",
              "Don't 크림·베이지 바탕으로 돌아가지 않는다(페이지 회색 #F3F3F2 유지).",
              "Don't 키트의 이미지·일러스트·아이콘을 가져오지 않는다.",
              "Don't 점 분포(strip plot), 범위 막대(fan) 같은 통계식 시각화를 쓰지 않는다."],
}

side = {
    'schemaVersion': 2,
    'generatedAt': datetime.datetime.now().isoformat(timespec='seconds'),
    'title': 'Design System: 인상안 협상 구간',
    'extensions': {
        'colorMeta': {k: {'role': r, 'displayName': n, 'canonical': h, 'tonalRamp': ramp(h)} for k, (r, n, h) in COLORS.items()},
        'typographyMeta': {'display': {'displayName': 'Display', 'purpose': '회사명, 회사 찾기 제목'},
                           'headline': {'displayName': 'Headline', 'purpose': '협상 구간 요약 줄의 숫자'},
                           'title': {'displayName': 'Title', 'purpose': '섹션 제목'},
                           'body': {'displayName': 'Body', 'purpose': '설명, 진단 문장'},
                           'label': {'displayName': 'Label', 'purpose': '축 눈금, 라벨, 탭, 배지'}},
        'shadows': [{'name': 'card', 'value': '0 4px 30px rgba(31,31,31,0.07)', 'purpose': '모든 카드·검색 칸·입력 묶음 (키트 규칙 blur 30 / y 4 / 7%)'},
                    {'name': 'small', 'value': '0 2px 12px rgba(31,31,31,0.06)', 'purpose': '분절 버튼 선택 칸, 스위치 손잡이'}],
        'motion': [{'name': 'ease-out-expo', 'value': 'cubic-bezier(0.16, 1, 0.3, 1)', 'purpose': '모든 상태 전환'},
                   {'name': 'state', 'value': '180ms', 'purpose': '버튼·탭·칩 hover, 스위치'},
                   {'name': 'range-glide', 'value': '350ms', 'purpose': '협상 구간 띠·눈금·점 이동 (서명 움직임)'}],
        'breakpoints': [{'name': 'phone-min', 'value': '360px'}, {'name': 'phone-max', 'value': '430px'}, {'name': 'frame', 'value': '520px'}],
    },
    'components': COMPONENTS,
    'narrative': NARRATIVE,
}

if __name__ == '__main__':
    p = os.path.join(ROOT, '.impeccable', 'design.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(side, f, ensure_ascii=False, indent=1)
    print('design.json', os.path.getsize(p), 'bytes')
