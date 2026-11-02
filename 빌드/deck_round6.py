# 덱 라운드6(11/2): 7장 뒤에 '기록이 기록을 부르는 흐름' 슬라이드 추가(→14장), 이후 배경 교차 맞춤. 사용: python3 deck_round6.py <덱.html>
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
assert 'data-title="기록이 기록을 부르는 흐름"' not in s, '이미 적용됨'
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)
# 배경 교차: 새 슬라이드(흰색) 뒤 9~11장을 회색·흰색·회색으로
sub('<section class="slide" data-app="grade"', '<section class="slide gray" data-app="grade"')
sub('<section class="slide gray" data-app="ranking"', '<section class="slide" data-app="ranking"')
sub('<section class="slide" data-app="my"', '<section class="slide gray" data-app="my"')
sub('<section class="slide gray" data-app="grade"', '''<section class="slide" data-app="detail/1" data-legacy="0" data-title="기록이 기록을 부르는 흐름" data-note="">
<div class="wrap demo"><p class="eyebrow t1" data-a>과제 1·2 연결 · 탐색 흐름</p><h2 class="h1" data-a>기록 하나가,<br>다음 기록을 부릅니다.</h2>
<ol class="loop">
<li data-a><b>1</b><span><strong>관찰 상세</strong>종 이름을 누르면</span></li>
<li data-a><b>2</b><span><strong>같은 종 모아보기</strong>제주 곳곳의 분포와 다른 사람의 기록</span></li>
<li data-a><b>3</b><span><strong>북마크·조회</strong>좋은 기록을 남긴 사람에게 포인트</span></li>
<li data-a><b>4</b><span><strong>탐험도</strong>기록이 적은 지역이 깃발로</span></li>
<li data-a class="back"><b>↺</b><span><strong>이 지역에서 기록하기</strong>탐사 보너스 +15P와 함께 새 기록으로</span></li>
</ol>
<p class="hint" data-a>기존 앱은 관찰 상세에서 흐름이 끝났어요.</p></div></section>

<section class="slide gray" data-app="grade"''')
sub('/* 라이브 시연 */', '''/* 기록이 기록을 부르는 흐름 */
.loop{margin:40px 0 0;padding:0;list-style:none;display:grid;gap:10px}
.loop li{position:relative;display:grid;grid-template-columns:48px 1fr;gap:20px;align-items:center;padding:14px 24px;border-radius:20px;background:var(--gray)}
.loop li+li::before{content:"";position:absolute;left:47px;top:-11px;width:2px;height:12px;background:#b7c4be}
.loop b{width:48px;height:48px;border-radius:50%;background:rgba(0,113,227,.12);color:var(--blue);display:flex;align-items:center;justify-content:center;font-size:22px}
.loop li.back{background:rgba(0,163,126,.10)}.loop li.back b{background:var(--green);color:#fff;font-size:26px}
.loop span{font-size:24px;font-weight:500;color:#3a3a3c;line-height:1.35}
.loop strong{font-weight:800;color:var(--ink);margin-right:12px}

/* 라이브 시연 */''')
open(p, 'w', encoding='utf-8').write(s); print('ok')
