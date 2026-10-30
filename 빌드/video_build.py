# 시연 영상 HTML 빌드: video_template.html + Pretendard(덱에서) + 최종 앱(base64)
# 사용: python3 video_build.py <덱.html> <최종앱.html> <출력.html>
import sys, re, base64, os
deck, app, out = sys.argv[1:4]
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, 'video_template.html'), encoding='utf-8').read()
font = re.search(r"@font-face\{font-family:'Pretendard Variable'.*?\}", open(deck, encoding='utf-8').read(), re.S).group(0)
b64 = base64.b64encode(open(app, 'rb').read()).decode()
for k, v in [('/*FONT*/', font), ('/*APP*/', b64)]:
    assert t.count(k) == 1, k
    t = t.replace(k, v)
open(out, 'w', encoding='utf-8').write(t)
print('ok', out, round(len(t) / 1e6, 1), 'MB')
