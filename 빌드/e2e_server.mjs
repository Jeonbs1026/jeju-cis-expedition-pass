// 서버 연동 종단 검사: 기기 A(청중)·기기 B(다른 사람 → 전문가) 두 브라우저로 실제 배포 주소 확인
// 사용: node e2e_server.mjs <전문가키> [주소]
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
const KEY = process.argv[2], URL_ = process.argv[3] || 'https://jeju-cis.jeju-cis.workers.dev/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ok = (c, m) => { console.log(c ? 'PASS' : 'FAIL', m); if (!c) process.exitCode = 1; };

async function browser(port) {
  const dir = mkdtempSync('/private/tmp/claude-501/cis-e2e-');
  const proc = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${dir}`, 'about:blank']);
  let ws; for (let i = 0; i < 50 && !ws; i++) { await sleep(300); try { const t = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((a, b) => { ws.onopen = a; ws.onerror = b; }); } catch { ws = null; } }
  let id = 0; const pend = {}, errors = [];
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description?.split('\n')[0]); pend[m.id]?.(m); };
  const send = (method, params = {}) => new Promise(r => { pend[++id] = r; ws.send(JSON.stringify({ id, method, params })); });
  const ev = async x => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result.result?.value;
  await send('Runtime.enable'); await send('Network.enable'); await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true, screenWidth: 390, screenHeight: 844 });
  await send('Page.navigate', { url: URL_ + '#/home' }); await sleep(3500);
  return { send, ev, errors, close() { ws.close(); proc.kill(); } };
}
const until = async (b, expr, ms = 15000) => { for (let t = 0; t < ms; t += 500) { if (await b.ev(expr)) return true; await sleep(500); } return false; };

const A = await browser(9350), B = await browser(9351);
// 1) A: 이름 모름으로 등록 → 서버 전송, 공개 검토 중
await A.ev(`setLegacy(false);startRecord();1`); await sleep(1500);
await A.ev(`samplePhoto();setLevel('unknown');draft.consent=true;1`); await sleep(300); await A.ev(`document.querySelector('#form-note').value='E2E 테스트 기록';submitRecord();1`);
ok(await until(A, `S.records.find(r=>r.note==='E2E 테스트 기록')?.sync==='done'`), 'A 등록 → 서버 전송 완료');
const srv = await A.ev(`S.records.find(r=>r.note==='E2E 테스트 기록').srv`);
await A.ev(`closeSheet();1`); await sleep(400);
ok(await A.ev(`document.querySelector('.sync-line b')?.textContent==='공개 검토 중'`), 'A 상세: 공개 검토 중 표시');
// 2) B(일반): 승인 전에는 안 보임
await B.ev(`syncNow()`); await sleep(1500);
ok(!(await B.ev(`S.records.some(r=>r.srv===${srv})`)), 'B: 승인 전 기록 안 보임');
// 3) B 전문가 로그인 → 검토 화면에서 승인 + 동정 완료
await B.ev(`expertLogin();1`); await B.ev(`document.querySelector('#expert-key').value='${KEY}';saveExpertKey()`); await sleep(2500);
ok(await B.ev(`location.hash==='#/review'&&!!document.querySelector('#rv-status-${srv}')`), 'B 전문가: 검토 화면에 A 기록');
ok(await B.ev(`(()=>{const im=[...document.querySelectorAll('.review-record img')][0];return im&&im.complete&&im.naturalWidth>0})()`) || await until(B, `[...document.querySelectorAll('.review-record img')].some(im=>im.naturalWidth>0)`, 5000), 'B 전문가: 승인 전 사진 보임');
await B.ev(`reviewApply(${srv},{public:1})`); await sleep(1500);
await B.ev(`document.querySelector('#rv-status-${srv}').value='done';document.querySelector('#rv-species-${srv}').value='청둥오리';reviewSave(${srv})`); await sleep(1500);
// 4) A: 상태·공개 알림 수신
await A.ev(`syncNow()`);
ok(await until(A, `S.records.find(r=>r.srv===${srv})?.status==='done'`), 'A: 동정 완료 반영');
ok(await A.ev(`S.notifications.slice(0,3).map(n=>n.title).join('|')`).then(t => /이름을 확인|공개되었어요/.test(t)), 'A: 결과·공개 알림 생성');
// 5) B 로그아웃 → 일반 회원으로 공개 기록 보임 (좌표는 낮춤)
await B.ev(`expertLogin();1`); await B.ev(`saveExpertKey(true)`); await sleep(2500);
ok(await until(B, `S.records.some(r=>r.srv===${srv}&&r.remote&&r.name==='청둥오리')`), 'B 일반: 승인 후 공개 기록 보임');
ok(await B.ev(`(()=>{const r=S.records.find(r=>r.srv===${srv});return Math.round(r.lat*100)/100===r.lat})()`), 'B 일반: 좌표 소수 2자리');
// 6) A 오프라인 등록 → 대기 → 온라인 복귀 후 전송
await A.send('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
await A.ev(`startRecord();1`); await sleep(1200);
await A.ev(`samplePhoto();1`); await sleep(300); await A.ev(`document.querySelector('#form-note').value='E2E 오프라인 기록';submitRecord();1`); await sleep(2500);
ok(await A.ev(`S.records.find(r=>r.note==='E2E 오프라인 기록')?.sync==='pending'`), 'A 오프라인: 기기에 저장, 전송 대기');
await A.ev(`closeSheet();1`); ok(await A.ev(`document.querySelector('.sync-line b')?.textContent==='서버 전송 대기'`), 'A 오프라인: 전송 대기 표시');
await A.send('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
await A.ev(`syncNow()`);
ok(await until(A, `S.records.find(r=>r.note==='E2E 오프라인 기록')?.sync==='done'`), 'A 온라인 복귀: 자동 전송');
const srv2 = await A.ev(`S.records.find(r=>r.note==='E2E 오프라인 기록').srv`);
// 정리: 테스트 기록 삭제
for (const id of [srv, srv2]) await fetch(`${URL_}api/records/${id}`, { method: 'DELETE', headers: { 'X-Expert-Key': KEY } });
console.log('errors A:', A.errors.length ? A.errors : 'none', ' B:', B.errors.length ? B.errors : 'none');
A.close(); B.close();
process.exit(process.exitCode||0);
