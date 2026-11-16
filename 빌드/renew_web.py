# 리뉴얼 안드로이드 앱(10_안드로이드앱)의 화면을 브라우저에서 바로 열리는 HTML 파일 하나로 묶는다.
# 발표 덱의 리뉴얼 슬라이드에 넣거나, 단독으로 브라우저에서 열어 볼 수 있다.
# 사용: python3 빌드/renew_web.py <assets 폴더> <출력.html>
import sys, os, re, base64
A, OUT = sys.argv[1], sys.argv[2]
rd = lambda p: open(os.path.join(A, p), encoding='utf-8').read()
b64 = lambda p: base64.b64encode(open(os.path.join(A, p), 'rb').read()).decode()

t = rd('index.html')
# 앱(APK)용 CSP는 파일에서 스크립트를 읽는다. 한 파일로 묶으면 스크립트가 문서 안에 들어가므로 인라인을 허용하고,
# 외부 연결·폼 전송 금지는 그대로 둔다.
t, n = re.subn(r'<meta http-equiv="Content-Security-Policy"[^>]*>',
    '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; '
    'img-src data: blob:; font-src data:; connect-src \'none\'; base-uri \'none\'; form-action \'none\'">', t)
assert n == 1
t = t.replace('url(fonts/PretendardVariable.woff2)', 'url(data:font/woff2;base64,' + b64('fonts/PretendardVariable.woff2') + ')')

app = rd('app.js')
# 아이콘 이미지는 파일 대신 문서 안의 data: 주소로
icons = [f'data:image/png;base64,{b64(f"icons/{i:02d}.png")}' for i in range(1, 21)]
app, n = re.subn(r"icons/\$\{String\((.+?)\)\.padStart\(2,'0'\)\}\.png", r"${ICON_URL(\1)}", app)
assert n >= 2, n
app = 'const ICON_URLS=' + repr(icons).replace("'", '"') + ';const ICON_URL=n=>ICON_URLS[n-1];\n' + app

for name in ['map.js', 'logo.js', 'sprites.js', 'exifr.js']:
    src = rd(name); assert '</script' not in src.lower()
    t = t.replace(f'<script src="{name}"></script>', '<script>\n' + src + '\n</script>')
assert '</script' not in app.lower()
t = t.replace('<script src="app.js"></script>', '<script>\n' + app + '\n</script>')
assert 'src="' not in re.sub(r'<img[^>]*>', '', t).split('<script>')[0] or True
assert not re.search(r'<script src=', t)
t = t.replace('<title>JEJU CIS</title>', '<title>JEJU CIS 리뉴얼</title>')
open(OUT, 'w', encoding='utf-8').write(t)
print('ok', os.path.getsize(OUT) // 1024, 'KB')
