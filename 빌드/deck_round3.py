# 발표 덱: 서버 연동 이후 문구 수정 + 라이브 시연(검수 후 공개) 슬라이드 추가. 사용: python3 deck_round3.py <덱.html>
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
assert 'data-app="review"' not in s, '이미 적용됨'
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)
sub('기록은 내 휴대폰에만 저장돼요', '올린 사진은 전문가가 확인한 뒤에 공개돼요')
sub('<span>HTML 파일 하나로 동작하는 웹앱 · 기록은 각자의 브라우저에 저장 · 실제 회원·서버와는 연결하지 않음</span>',
    '<span>HTML 파일 하나로 된 웹앱과 시연용 서버(기록 공유·전문가 검토) · 실제 JEJU CIS 회원·서버와는 연결하지 않음 · 운영 앱에 이 서버 구성을 제안하는 것은 아님</span>')
sub('<li>나의 탐험 리포트</li>', '<li>나의 탐험 리포트</li><li>전문가 검수 후 공개되는 기록 공유</li>')
sub('<section class="slide gray" data-title="연구소가 이어받을 수 있게"',
    '''<section class="slide dark" data-app="review" data-legacy="0" data-title="라이브 시연: 검수 후 공개" data-note="이제 직접 해 보겠습니다. QR로 들어오신 분 중 한 분이 이름을 모르는 생물 사진을 올려 주세요. 올린 사진은 제가 승인하기 전까지 올리신 분과 전문가만 볼 수 있습니다. 오른쪽 전문가 화면에서 사진을 확인해 공개를 승인하고 동정 결과를 저장하면, 올리신 분 휴대폰에 결과 알림이 도착합니다. 알림은 앱을 열어 둔 상태에서 십여 초 안에 옵니다.
(사전 준비: 리허설 때 이 화면에서 전문가 키로 로그인해 두기. 새 기록이 안 보이면 오른쪽 위 '새로고침')">
<div class="glow" style="--c:#34c759;width:760px;height:560px;left:-160px;top:220px"></div>
<div class="wrap demo"><p class="eyebrow t3" data-a>라이브 시연 · 검수 후 공개</p><h2 class="h1" data-a>방금 올린 기록,<br>지금 확인합니다.</h2>
<div class="live-steps"><div data-a><b>1</b><span><strong>청중</strong>휴대폰으로 이름 모르는 생물을 등록해요</span></div><div data-a><b>2</b><span><strong>발표자</strong>전문가 화면에서 사진을 보고 공개 승인·동정해요</span></div><div data-a><b>3</b><span><strong>청중</strong>휴대폰에 결과 알림이 도착해요</span></div></div>
<p class="safe" data-a>올린 사진은 전문가가 승인하기 전까지 올린 사람과 전문가만 볼 수 있어요.</p></div></section>

<section class="slide gray" data-title="연구소가 이어받을 수 있게"''')
sub('/* 이어받기 */', '''/* 라이브 시연 */
.live-steps{margin-top:46px;display:grid;gap:18px}
.live-steps div{display:grid;grid-template-columns:56px 1fr;gap:22px;align-items:center;padding:22px 26px;border-radius:24px;background:#1c1c1e}
.live-steps b{width:56px;height:56px;border-radius:50%;background:#30d158;color:#000;display:flex;align-items:center;justify-content:center;font-size:24px}
.live-steps span{font-size:28px;font-weight:600;color:#f5f5f7;line-height:1.4}
.live-steps strong{display:block;font-size:18px;color:#86868b;margin-bottom:2px}
.safe{margin-top:26px;font-size:21px;color:#86868b;font-weight:600}

/* 이어받기 */''')
sub('<p>동정 완료 후 수정·삭제 제한, 포인트 중복 지급 방지, 희귀종 위치 보호.</p>', '<p>검수 후 공개, 동정 완료 후 수정·삭제 제한, 포인트 중복 지급 방지, 희귀종 위치 보호.</p>')
open(p, 'w', encoding='utf-8').write(s); print('ok')
