# 발표 덱 끝(마무리 앞)에 '리뉴얼 디자인' 슬라이드 3장을 넣는다.
#  1) 화면 4장  2) 덱 안에서 직접 눌러 보는 리뉴얼 앱  3) 픽셀 도감 25종과 앱 아이콘 20종
# 사용: python3 빌드/deck_renew.py <덱.html> <리뉴얼앱_웹.html> <assets 폴더> <스크린샷 폴더>
import sys, os, re, io, base64, html
from PIL import Image
DECK, WEB, A, SHOTS = sys.argv[1:5]
t = open(DECK, encoding='utf-8').read()
assert 'data-renew' not in t, '이미 리뉴얼 슬라이드가 들어 있습니다'

def rep(a, b):
    global t
    assert t.count(a) == 1, (t.count(a), a[:80]); t = t.replace(a, b)
def jpg(path, w):
    im = Image.open(path).convert('RGB'); im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=86, optimize=True); return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
note = lambda s: html.escape(s, quote=True)

# 그림 재료: 삽화(sprites.js)와 종 이름(app.js), 아이콘 이름(app.js)
SPR = re.findall(r'"(data:image/png;base64,[^"]+)"', open(os.path.join(A, 'sprites.js'), encoding='utf-8').read())
app = open(os.path.join(A, 'app.js'), encoding='utf-8').read()
NAMES = re.findall(r"\{name:'([^']+)',taxon:", app)
assert len(SPR) == len(NAMES) == 26, (len(SPR), len(NAMES))
ICON_NAMES = re.findall(r'"([^"]+)"', re.search(r'const ICON_NAMES=(\[[^\]]+\])', app).group(1))
ICONS = ['data:image/png;base64,' + base64.b64encode(open(os.path.join(A, f'icons/{i:02d}.png'), 'rb').read()).decode() for i in range(1, 21)]

CSS = '''
/* 리뉴얼 디자인 */
.rn-shots{margin-top:40px;display:flex;justify-content:center;gap:48px}
.rn-shots figure{margin:0;display:flex;flex-direction:column;align-items:center;gap:18px}
.rn-shots .frame{width:252px;height:536px;border-radius:40px;background:#2c2c2e;padding:8px;box-shadow:inset 0 0 0 2px #48484a,0 30px 60px -30px rgba(0,0,0,.8)}
.rn-shots img{display:block;width:236px;height:520px;border-radius:32px;object-fit:cover;object-position:top}
.rn-shots figcaption{text-align:center;font-size:21px;font-weight:700;color:#f5f5f7;line-height:1.35}
.rn-shots figcaption span{display:block;font-size:17px;font-weight:500;color:#86868b}
.rn-list{margin-top:40px;display:grid;gap:14px}
.rn-list div{display:grid;grid-template-columns:200px 1fr;gap:20px;align-items:center;padding:18px 26px;border-radius:22px;background:var(--gray)}
.rn-list b{font-size:24px;font-weight:800;letter-spacing:-.02em}
.rn-list span{font-size:23px;font-weight:500;color:#3a3a3c;line-height:1.4}
.rn-art{margin-top:36px;display:grid;grid-template-columns:780px 1fr;gap:24px;flex:1;min-height:0}
.rn-art .card{padding:28px 32px;display:flex;flex-direction:column}
.rn-art h3{font-size:26px;font-weight:800;letter-spacing:-.02em;display:flex;justify-content:space-between;align-items:baseline}
.rn-art h3 small{font-size:18px;font-weight:600;color:var(--sub)}
.rn-dex{margin-top:18px;display:grid;grid-template-columns:repeat(7,1fr);gap:10px 6px}
.rn-dex div{display:flex;flex-direction:column;align-items:center;gap:2px;font-size:14px;font-weight:700;color:#3a3a3c;text-align:center;line-height:1.15;letter-spacing:-.03em}
.rn-dex img{width:84px;height:84px;image-rendering:pixelated}
.rn-icons{margin-top:18px;display:grid;grid-template-columns:repeat(5,1fr);gap:16px 14px}
.rn-icons img{width:100%;aspect-ratio:1;border-radius:24%;display:block;box-shadow:0 0 0 1px rgba(0,0,0,.08)}
.rn-icons .def{position:relative}
.rn-icons .def::after{content:"기본";position:absolute;right:-8px;top:-8px;background:var(--ink);color:#fff;font-size:12px;font-weight:800;border-radius:999px;padding:3px 8px}
'''
rep('.pg{position:absolute;', CSS + '.pg{position:absolute;')
for a, b in [('#phone{position:absolute;', '#phone,#phone2{position:absolute;'), ('#phone.on{', '#phone.on,#phone2.on{'),
             ('#phone .screen{', '#phone .screen,#phone2 .screen{'), ('#app{position:absolute;', '#app,#renew{position:absolute;'),
             ('#phone .loading{', '#phone .loading,#phone2 .loading{')]:
    rep(a, b)

shots = ''.join(f'<figure data-a><div class="frame"><img src="{jpg(os.path.join(SHOTS, f + ".png"), 472)}" alt="리뉴얼 앱 {c} 화면"></div><figcaption>{c}<span>{s}</span></figcaption></figure>'
                for f, c, s in [('home', '홈', '벤토 카드 · 2열 피드'), ('map', '생태지도', '읍·면·동까지만 공개'), ('detail', '기록 상세', '북마크 · 동정 의견'), ('my', '내정보', '등급 · 내 도감 25종')])
dex = ''.join(f'<div><img src="{SPR[i]}" alt="">{NAMES[i]}</div>' for i in range(26) if i != 6)
icons = ''.join(f'<div{" class=\"def\"" if i == 9 else ""}><img src="{ICONS[i]}" alt="{ICON_NAMES[i]}"></div>' for i in range(20))

S1 = f'''<section class="slide dark" data-title="리뉴얼 디자인" data-note="{note("여기서부터는 공모전 과제와 별도로 준비한 리뉴얼 디자인입니다. 원본 CIS 앱의 화면 구성인 홈, 생태지도, 기록 상세, 내정보를 그대로 따르면서 디자인을 새로 만든 안드로이드 앱입니다. 큰 글씨와 카드, 화면 아래에 떠 있는 탭, 먹색·파랑·라임 세 가지 색으로 정리했습니다.")}">
<div class="glow" style="--c:#0a84ff;width:1000px;height:600px;left:300px;top:260px;opacity:.35"></div>
<div class="wrap"><p class="eyebrow" data-a>리뉴얼 디자인</p><h2 class="h1" data-a>같은 구조, <span class="grad">새로운 얼굴.</span></h2>
<div class="rn-shots">{shots}</div></div></section>

<section class="slide" data-renew="1" data-title="리뉴얼 앱 직접 보기" data-note="{note("[동작] 오른쪽 휴대폰은 리뉴얼 앱입니다. 첫 실행 안내를 넘기고, 홈의 기록 카드 → 기록 상세 → 아래 지도 탭 순으로 눌러 봅니다.\n\n사진 한 장을 고르면 사진에 저장된 촬영 위치와 일시가 자동으로 채워지고, 지도와 상세 화면에는 읍·면·동까지만 표시됩니다. 기록할 때마다 내 도감의 제주 생물 25종이 하나씩 채워집니다.\n이 앱은 인터넷 없이 동작하고, 안드로이드 설치 파일은 연구소에 따로 전달드립니다.\n\n[시연 전] 오른쪽 아래 ↺를 누르면 리뉴얼 앱이 첫 실행 상태로 돌아갑니다.")}">
<div class="wrap demo"><p class="eyebrow" data-a>리뉴얼 디자인 · 안드로이드 앱</p><h2 class="h1" data-a>직접 눌러 보는<br>리뉴얼 앱.</h2>
<div class="rn-list"><div data-a><b>한 장으로 기록</b><span>사진에 저장된 촬영 위치·일시를 읽어 자동 입력</span></div>
<div data-a><b>위치 보호</b><span>지도와 상세에는 읍·면·동까지만 표시</span></div>
<div data-a><b>한눈에 보는 홈</b><span>이번 달 기록·등급·포인트 카드와 2열 피드</span></div>
<div data-a><b>내 도감</b><span>기록할 때마다 제주 생물 25종이 채워짐</span></div>
<div data-a><b>부드러운 화면</b><span>첫 실행 안내 3장, 화면 전환 애니메이션</span></div></div>
<p class="hint" data-a>인터넷 없이 동작 · 안드로이드 설치 파일(APK)은 연구소에 따로 전달</p></div></section>

<section class="slide gray" data-title="픽셀 도감과 앱 아이콘" data-note="{note("리뉴얼 앱에 들어간 그림입니다. 제주 생물 25종을 픽셀 그림으로 만들어, 기록할 때마다 내 도감에 하나씩 채워지게 했습니다. 앱 아이콘은 스무 가지 중 설정에서 고를 수 있고, 기본은 픽셀 노루입니다.")}">
<div class="wrap"><p class="eyebrow" data-a>리뉴얼 디자인 · 그림</p><h2 class="h1" data-a>제주 생물 25종, 앱 아이콘 20종.</h2>
<div class="rn-art"><div class="card" data-a><h3>픽셀 도감<small>포유류·조류·양서류·파충류·곤충</small></h3><div class="rn-dex">{dex}</div></div>
<div class="card" data-a><h3>앱 아이콘<small>설정에서 선택</small></h3><div class="rn-icons">{icons}</div></div></div></div></section>

'''
rep('<section class="slide dark" data-title="마무리"', S1 + '<section class="slide dark" data-title="마무리"')

rep('<iframe id="app" title="JEJU CIS 최종 앱"></iframe></div></div>',
    '<iframe id="app" title="JEJU CIS 최종 앱"></iframe></div></div>\n<div id="phone2" aria-label="리뉴얼 앱 시연 화면"><div class="screen"><div class="loading">리뉴얼 앱을 불러오는 중…</div><iframe id="renew" title="JEJU CIS 리뉴얼 앱"></iframe></div></div>')

webb64 = base64.b64encode(open(WEB, 'rb').read()).decode()
rep('<script type="text/plain" id="appB64">', f'<script type="text/plain" id="renewB64">{webb64}</script>\n<script type="text/plain" id="appB64">')

rep("function showApp(s){const route=s.dataset.app;byId('phone').classList.toggle('on',!!route);",
    "function showApp(s){const route=s.dataset.app;byId('phone').classList.toggle('on',!!route);byId('phone2').classList.toggle('on',!!s.dataset.renew);")
rep("byId('resetBtn').onclick=()=>{if(!appWin?.CIS)return;",
    """// 리뉴얼 앱: 같은 방식(srcdoc)으로 따로 불러온다. 저장 키(cis.*)는 기존 앱(jeju-cis-*)과 겹치지 않는다
const rframe=byId('renew');let renewWin=null;
function loadRenew(){if(rframe.srcdoc)return;const bin=atob(byId('renewB64').textContent.trim());rframe.srcdoc=new TextDecoder().decode(Uint8Array.from(bin,c=>c.charCodeAt(0)))}
rframe.addEventListener('load',()=>{renewWin=rframe.contentWindow;document.querySelector('#phone2 .loading')?.remove();
 renewWin.addEventListener('keydown',e=>{if(e.target.closest?.('input,textarea,select'))return;if(['ArrowRight','PageDown','ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();go(cur+(['ArrowRight','PageDown'].includes(e.key)?1:-1))}})});
function resetRenew(){try{Object.keys(localStorage).filter(k=>k.startsWith('cis.')).forEach(k=>localStorage.removeItem(k))}catch{}renewWin?.location.reload()}
byId('resetBtn').onclick=()=>{if(slides[cur].dataset.renew){resetRenew();toast('리뉴얼 앱을 첫 실행 상태로 돌렸어요.');return}if(!appWin?.CIS)return;""")
rep("if(next.dataset.app)loadApp();showApp(next);", "if(next.dataset.app)loadApp();if(next.dataset.renew)loadRenew();showApp(next);")
rep("setTimeout(loadApp,1500);", "setTimeout(loadApp,1500);setTimeout(loadRenew,4000);")
open(DECK, 'w', encoding='utf-8').write(t)
print('ok', os.path.getsize(DECK) // 1024, 'KB', '| slides', t.count('<section class="slide'))
