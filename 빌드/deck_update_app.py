# 발표 덱(JEJU_CIS_최종발표.html) 안에 내장된 앱을 최신 JEJU_CIS_최종.html로 교체
# 사용: python3 deck_update_app.py <덱.html> <앱.html>
import sys, re, base64
deck, app = sys.argv[1:3]
s = open(deck, encoding='utf-8').read()
b64 = base64.b64encode(open(app, 'rb').read()).decode()
s, n = re.subn(r'(<script type="text/plain" id="appB64">)[A-Za-z0-9+/=\s]*(</script>)', lambda m: m.group(1) + b64 + m.group(2), s)
assert n == 1, n
open(deck, 'w', encoding='utf-8').write(s)
print('ok', deck, round(len(s) / 1e6, 1), 'MB')
