# 시연 영상 효과음 트랙 합성 (영상 HTML의 Web Audio 소리와 같은 모양). numpy 없이 표준 라이브러리만 사용
# 사용: python3 sfx_mix.py <events.json> <길이(초)> <출력.wav>
#   events.json = [{"type": "tap"|"toggle"|"scene"|"chime", "t": 초}, ...]
import sys, json, math, random, wave, array
ev_path, total, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
SR = 44100
buf = array.array('f', [0.0]) * int(SR * (total + 1))

def tone(at, f0, f1, dur, gain, shape='sine'):
    n, phase, k = int(dur * SR), 0.0, math.log(1e-4 / gain) / (dur * SR)   # 지수 감쇠: gain → 0.0001
    for i in range(n):
        f = f0 * (f1 / f0) ** (i / n)
        phase += 2 * math.pi * f / SR
        w = math.sin(phase) if shape == 'sine' else 2 / math.pi * math.asin(math.sin(phase))
        j = int(at * SR) + i
        if j < len(buf): buf[j] += w * gain * math.exp(k * i)

def whoosh(at, dur=0.45, gain=0.16, q=1.2):
    # 사인 창을 씌운 잡음 → 300→2200Hz로 올라가는 대역 통과 필터
    n = int(dur * SR); x1 = x2 = y1 = y2 = 0.0; rnd = random.Random(7)
    for i in range(n):
        if i % 32 == 0:
            fc = 300 * (2200 / 300) ** (i / n); w0 = 2 * math.pi * fc / SR; al = math.sin(w0) / (2 * q)
            b0, b2, a0, a1, a2 = al, -al, 1 + al, -2 * math.cos(w0), 1 - al
        x = (rnd.random() * 2 - 1) * math.sin(math.pi * i / n)
        y = (b0 * x + b2 * x2 - a1 * y1 - a2 * y2) / a0
        x2, x1, y2, y1 = x1, x, y1, y
        j = int(at * SR) + i
        if j < len(buf): buf[j] += y * gain

for e in json.load(open(ev_path)):
    t, kind = max(0.0, e['t']), e['type']
    if kind == 'tap': tone(t, 1150, 650, 0.07, 0.22)
    elif kind == 'toggle': tone(t, 660, 660, 0.09, 0.14, 'tri'); tone(t + 0.09, 990, 990, 0.12, 0.14, 'tri')
    elif kind == 'scene': whoosh(t)
    elif kind == 'chime': tone(t, 1047, 1047, 0.9, 0.12); tone(t + 0.12, 1319, 1319, 0.9, 0.10)

peak = max(1e-6, max(abs(v) for v in buf)) / 0.8   # 가장 큰 소리를 약 -2dB에 맞춤 (작으면 키우고, 겹쳐 크면 줄임)
pcm = array.array('h', (int(max(-1, min(1, v / peak)) * 32767) for v in buf[:int(SR * total)]))
with wave.open(out, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok', out, len(json.load(open(ev_path))), 'sounds', round(total, 1), 's')
