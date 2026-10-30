# 발표대본.md의 장별 내용을 덱의 발표 메모(data-note)로 넣음. 사용: python3 deck_notes.py <덱.html> <발표대본.md>
import sys, re, html
deck, md = sys.argv[1:3]
s = open(deck, encoding='utf-8').read(); t = open(md, encoding='utf-8').read()
parts = re.findall(r'^## (\d+)\. [^\n]*\n(.*?)(?=^## |^---)', t, re.S | re.M)
notes = {int(n): re.sub(r'\*\*', '', body).strip() for n, body in parts}
slides = list(re.finditer(r'<section class="slide[^"]*"[^>]*?data-note="[^"]*"', s))
assert len(slides) == len(notes) == 13, (len(slides), len(notes))
out, pos = [], 0
for i, m in enumerate(slides, 1):
    tag = m.group(0)
    new = re.sub(r'data-note="[^"]*"', 'data-note="' + html.escape(notes[i], quote=True) + '"', tag)
    out += [s[pos:m.start()], new]; pos = m.end()
s = ''.join(out) + s[pos:]
open(deck, 'w', encoding='utf-8').write(s); print('notes', len(notes))
