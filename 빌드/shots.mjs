// HTML 파일 여러 개를 Chrome으로 열어 화면을 찍는다(가상 시간을 쓰지 않아 계속 도는 애니메이션이 있어도 멈추지 않음).
// 사용: node 빌드/shots.mjs <너비> <높이> <배율> <대기ms> <html절대경로:출력png> ...
import { spawn } from 'node:child_process'; import { mkdtempSync, writeFileSync } from 'node:fs'; import { tmpdir } from 'node:os';
const [w, h, scale, wait, ...jobs] = process.argv.slice(2); const sleep = ms => new Promise(r => setTimeout(r, ms));
const port = 9300 + Math.floor(Math.random() * 400);
const p = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync(tmpdir() + '/shots-')}`, '--allow-file-access-from-files', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
let ws; for (let i = 0; i < 60 && !ws; i++) { await sleep(250); try { const t = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((r, j) => { ws.onopen = r; ws.onerror = j }) } catch { ws = null } }
let id = 0; const pend = {}, errs = []; ws.onmessage = e => { const m = JSON.parse(e.data); if (m.method === 'Runtime.exceptionThrown') errs.push(m.params.exceptionDetails.exception?.description?.split('\n')[0]); if (pend[m.id]) { pend[m.id](m); delete pend[m.id] } };
const send = (method, params = {}) => new Promise(r => { pend[++id] = r; ws.send(JSON.stringify({ id, method, params })) });
await send('Runtime.enable'); await send('Page.enable');
await send('Emulation.setDeviceMetricsOverride', { width: +w, height: +h, deviceScaleFactor: +scale, mobile: false });
for (const job of jobs) {
  const k = job.lastIndexOf(':'); const html = job.slice(0, k), out = job.slice(k + 1);
  await send('Page.navigate', { url: 'file://' + html }); await sleep(+wait);
  const r = await send('Page.captureScreenshot', { format: 'png' }); writeFileSync(out, Buffer.from(r.result.data, 'base64')); console.log('shot', out.split('/').pop());
}
console.log('errors:', errs.length ? errs : '없음'); ws.close(); p.kill(); process.exit(0);
