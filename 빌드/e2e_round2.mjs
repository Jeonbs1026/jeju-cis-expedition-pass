// 남은 기획 1~5 종단 검사 (실제 배포 주소, 기기 A·B). 사용: node e2e_round2.mjs <전문가키> [주소]
import { spawn } from 'node:child_process';
import { mkdtempSync } from 'node:fs';
const KEY = process.argv[2], URL_ = process.argv[3] || 'https://jeju-cis.jeju-cis.workers.dev/';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const ok = (c, m) => { console.log(c ? 'PASS' : 'FAIL', m); if (!c) process.exitCode = 1; };
const procs = [];
async function browser(port) {
  const proc = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-e2e2-')}`, 'about:blank']); procs.push(proc);
  let ws; for (let i = 0; i < 50 && !ws; i++) { await sleep(300); try { const t = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise((a, b) => { ws.onopen = a; ws.onerror = b; }); } catch { ws = null; } }
  let id = 0; const pend = {}, errors = [];
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description?.split('\n')[0]); pend[m.id]?.(m); };
  const send = (method, params = {}) => new Promise(r => { pend[++id] = r; ws.send(JSON.stringify({ id, method, params })); });
  const ev = async x => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result.result?.value;
  await send('Runtime.enable'); await send('Page.enable'); await send('Network.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true, screenWidth: 390, screenHeight: 844 });
  await send('Browser.grantPermissions', { permissions: ['geolocation'], origin: new URL(URL_).origin });
  await send('Emulation.setGeolocationOverride', { latitude: 33.4565, longitude: 126.5615, accuracy: 20 });
  await send('Page.navigate', { url: URL_ + '#/home' }); await sleep(3500);
  return { send, ev, errors };
}
const until = async (b, expr, ms = 20000) => { for (let t = 0; t < ms; t += 500) { if (await b.ev(expr)) return true; await sleep(500); } return false; };
const A = await browser(9360), B = await browser(9361);
await A.ev(`setLegacy(false);1`); await B.ev(`setLegacy(false);1`);

// 1) 전문가 보기 = 로그인일 때만
await A.ev(`S.viewer='expert';save();location.hash='#/detail/1';1`); await sleep(1200);
ok(!(await A.ev(`!!document.querySelector('.exact-row')`)), '1 로그인 없이 S.viewer만 바꿔도 정확 위치 안 보임');
await A.ev(`locationSheet();1`); ok(await A.ev(`!document.querySelector('.sheet [onclick*="S.viewer"]')&&!!document.querySelector('.sheet .btn')`), '1 위치 공개 시트: 보기 전환 없음, 로그인 버튼'); await A.ev(`closeSheet();1`);

// 3) 등록 시작 시 현재 위치 → 읍·면·동
await A.ev(`startRecord();1`);
ok(await until(A, `draft&&draft.located&&/아라동/.test(draft.region)`, 8000), '3 등록 시작 → 권한 있으면 현재 위치를 읍·면·동으로 (' + await A.ev(`draft?.region`) + ')');
ok(await A.ev(`!document.querySelector('.locate-banner')`), '3 위치를 채운 뒤 안내 버튼 숨김');
await A.send('Emulation.setGeolocationOverride', { latitude: 37.5665, longitude: 126.978, accuracy: 20 });
await A.ev(`requestLocation();1`); await sleep(1500);
ok(await A.ev(`/제주 밖/.test(document.querySelector('#toast').textContent)&&/아라동/.test(draft.region)`), '3 제주 밖 위치는 거부하고 기존 위치 유지');
await A.send('Emulation.setGeolocationOverride', { latitude: 33.4565, longitude: 126.5615, accuracy: 20 });

// 4) 포인트 애니메이션 · 홈 미션 위젯
await A.ev(`samplePhoto();1`); await sleep(300); await A.ev(`document.querySelector('#form-note').value='E2E2 기록';submitRecord();1`); await sleep(500);
ok(await A.ev(`!!document.querySelector('.sheet .earned.pop .earn-num')`), '4 등록 완료 시 포인트 애니메이션');
await sleep(900); ok(await A.ev(`(()=>{const t=document.querySelector('.sheet .earn-num')?.textContent;return Number(t)>0})()`), '4 숫자가 최종 적립값까지 올라감');
await A.ev(`closeSheet();location.hash='#/home';1`); await sleep(800);
ok(await A.ev(`/이번 주 탐사 미션/.test(document.querySelector('.home-mission')?.textContent||'')`), '4 홈 주간 미션 위젯');
await A.ev(`document.querySelector('.home-mission').click();1`); await sleep(500); ok(await A.ev(`location.hash==='#/missions'`), '4 위젯 → 미션 화면');

// 5) 출석 포인트·연속 보너스, 배지 12종
ok(await A.ev(`pointLog().some(x=>x.label.startsWith('출석'))`), '5 오늘 출석 포인트');
const today = await A.ev(`localNow().slice(0,10)`), d = n => new Date(Date.parse(today) - n * 864e5).toISOString().slice(0, 10);
await A.ev(`S.visits=['${d(2)}','${d(1)}','${today}'];1`);
ok(await A.ev(`pointLog().some(x=>x.label==='3일 연속 출석')`), '5 3일 연속 출석 보너스');
ok(await A.ev(`badges().length===12&&Object.keys(BADGE_INFO).length===12`), '5 배지 12종(분류·지역·정확도 추가)');
await A.ev(`location.hash='#/badges';1`); await sleep(500); ok(await A.ev(`document.querySelectorAll('.badge-card').length===12`), '5 배지 컬렉션 12장');

// 2) 오동정 제보 → 전문가 처리 → 제보자 알림
ok(await until(A, `S.records.find(r=>r.note==='E2E2 기록')?.sync==='done'`), '준비: A 기록 서버 전송');
const srv = await A.ev(`S.records.find(r=>r.note==='E2E2 기록').srv`);
await A.ev(`reportRecord(2);document.querySelector('#report-note').value='E2E2 제보: 부리 색이 달라요';submitReport(2);1`);
ok(await until(A, `S.reports?.some(p=>p.note.startsWith('E2E2')&&p.sync==='done')`), '2 제보 서버 전송');
await B.ev(`expertLogin();1`); await B.ev(`document.querySelector('#expert-key').value='${KEY}';saveExpertKey()`); await sleep(2500);
await B.ev(`state.reviewTab='reports';render();1`); await sleep(500);
const rid = await B.ev(`SERVER.reports.find(x=>x.note.startsWith('E2E2'))?.srv`);
ok(!!rid && await B.ev(`!!document.querySelector('#rp-reply-${rid}')`), '2 전문가 검토: 오동정 제보 탭에 표시');
await B.ev(`document.querySelector('#rp-reply-${rid}').value='확인해서 고쳤어요';reportApply(${rid},'accepted')`); await sleep(1500);
await A.ev(`syncNow()`);
ok(await until(A, `S.reports.find(p=>p.srv===${rid})?.status==='accepted'`), '2 제보자: 반영됨 상태');
ok(await A.ev(`S.notifications.some(n=>n.title==='제보가 반영되었어요')`), '2 제보자: 알림');
await A.ev(`state.activity='reports';location.hash='#/activity';1`); await sleep(600);
ok(await A.ev(`/반영됨/.test(document.querySelector('.activity-list').textContent)&&/확인해서 고쳤어요/.test(document.querySelector('.activity-list').textContent)`), '2 활동내역 제보 탭: 반영됨·답변');

// 5) 받은 북마크 → 작성자 포인트 (공개 후 B가 북마크)
await B.ev(`reviewApply(${srv},{public:1})`); await sleep(1500);
await B.ev(`saveExpertKey(true)`); await sleep(2500);
ok(await until(B, `S.records.some(r=>r.srv===${srv}&&r.remote)`), '준비: B 일반 회원에게 공개 기록 보임');
await B.ev(`toggleBookmark(SRV_ID+${srv});1`); await sleep(1500);
await A.ev(`syncNow()`);
ok(await until(A, `S.records.find(r=>r.srv===${srv})?.bookmarks===1`), '5 A: 받은 북마크 1');
ok(await A.ev(`pointLog().some(x=>x.label.startsWith('받은 북마크'))`), '5 A: 받은 북마크 포인트');

await fetch(`${URL_}api/records/${srv}`, { method: 'DELETE', headers: { 'X-Expert-Key': KEY } });
console.log('errors A:', A.errors.length ? A.errors : 'none', ' B:', B.errors.length ? B.errors : 'none');
procs.forEach(p => p.kill()); process.exit(process.exitCode || 0);
