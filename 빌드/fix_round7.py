# 라운드7(11/2): 전문가 검토 화면에서 승인 전·비공개 사진을 흐리게, 눌러야 보임(발표 화면에 부적절한 사진 노출 방지). 사용: python3 fix_round7.py <앱.html>
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)
sub('<img src="${photoUrl(x)}" alt="검토할 관찰 사진">',
    '''<img src="${photoUrl(x)}" alt="검토할 관찰 사진" class="${x.public===1||REVEAL.has(x.srv)?'':'blur-photo'}" onclick="REVEAL.add(${x.srv});this.classList.remove('blur-photo')">''')
sub("<b class=\"pub-state\">${x.public===1?'공개 중':x.public===-1?'비공개 처리':'공개 검토 대기'}</b>",
    "<b class=\"pub-state\">${x.public===1?'공개 중':x.public===-1?'비공개 처리':'공개 검토 대기'}</b>${x.public!==1&&!REVEAL.has(x.srv)?'<span class=\"hint blur-hint\">사진을 눌러야 보여요</span>':''}")
sub('async function reviewApply(', 'const REVEAL=new Set();\nasync function reviewApply(')
sub('.review-record.is-hidden{opacity:.7}', '.review-record.is-hidden{opacity:.7}\n.review-record img.blur-photo{filter:blur(12px) grayscale(1);clip-path:inset(0 round 10px);cursor:pointer}\n.review-record .blur-hint{display:block;margin-top:2px}')
open(p, 'w', encoding='utf-8').write(s); print('ok')
