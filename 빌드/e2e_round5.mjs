// 라운드5 검사: 서버에서 삭제된 내 기록 표시·재등록, 서버 글자 거르기(XSS). 사용: node e2e_round5.mjs <전문가키> [주소]
import { spawn, execFileSync } from 'node:child_process';import { mkdtempSync } from 'node:fs';
const KEY=process.argv[2],URL_=process.argv[3]||'https://jeju-cis.jeju-cis.workers.dev/';const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const ok=(c,m)=>{console.log(c?'PASS':'FAIL',m);if(!c)process.exitCode=1};const procs=[];
async function browser(port){const proc=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new',`--remote-debugging-port=${port}`,`--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-r5-')}`,'about:blank']);procs.push(proc);
 let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
 let id=0;const pend={},errors=[];ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description?.split('\n')[0]);pend[m.id]?.(m)};
 const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});const ev=async x=>(await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true})).result.result?.value;
 await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true,screenWidth:390,screenHeight:844});
 await send('Page.navigate',{url:URL_+'#/home'});await sleep(3500);return {ev,errors}}
const until=async(b,expr,ms=20000)=>{for(let t=0;t<ms;t+=500){if(await b.ev(expr))return true;await sleep(500)}return false};
const d1=sql=>execFileSync('npx',['wrangler','d1','execute','jeju-cis-db','--remote','--command',sql],{cwd:decodeURIComponent(new URL('../배포/',import.meta.url).pathname),stdio:'pipe'});
const A=await browser(9370),B=await browser(9371);await A.ev(`setLegacy(false);1`);await B.ev(`setLegacy(false);1`);
// 1) 서버에서 삭제된 내 기록
await A.ev(`startRecord();1`);await sleep(1200);await A.ev(`samplePhoto();1`);await sleep(300);await A.ev(`document.querySelector('#form-note').value='R5 삭제 검사';submitRecord();1`);
ok(await until(A,`S.records.find(r=>r.note==='R5 삭제 검사')?.sync==='done'`),'준비: A 기록 서버 전송');
const srv=await A.ev(`S.records.find(r=>r.note==='R5 삭제 검사').srv`),lid=await A.ev(`S.records.find(r=>r.note==='R5 삭제 검사').id`);
await fetch(`${URL_}api/records/${srv}`,{method:'DELETE',headers:{'X-Expert-Key':KEY}});
await A.ev(`closeSheet();syncNow()`);
ok(await until(A,`S.records.find(r=>r.id===${lid})?.sync==='gone'`),'1 전문가가 삭제 → A 기록 상태 gone');
await A.ev(`location.hash='#/detail/${lid}';render();1`);await sleep(600);ok(await A.ev(`document.querySelector('.sync-line b')?.textContent==='서버에서 삭제됨'`),'1 상세에 "서버에서 삭제됨"');
await A.ev(`editRecord(${lid});1`);await sleep(1200);await A.ev(`submitRecord();1`);
ok(await until(A,`(()=>{const r=S.records.find(r=>r.id===${lid});return r?.sync==='done'&&r.srv&&r.srv!==${srv}})()`),'1 삭제된 기록을 고쳐 저장 → 새 기록으로 재등록');
const srv2=await A.ev(`S.records.find(r=>r.id===${lid}).srv`);
// 2) XSS: 서버 검사를 우회해 DB에 직접 넣은 따옴표 이름
d1(`INSERT INTO records (device,nickname,taxon,name,name_level,scientific,status,lat,lon,region,observed_at,created_at,note,photo,public,updated_at) VALUES ('test-device-xss2','해커<b>','bird','x'');window.__pwn=1;(''','species','','recorded',33.45,126.56,'제주시 아라동','2026-10-30T10:00','2026-10-30T10:00','R5XSS','data:image/jpeg;base64,/9j/',1,'2026-10-30T10:00'); UPDATE meta SET v=v+1 WHERE k='version';`);
await B.ev(`syncNow()`);ok(await until(B,`S.records.some(r=>r.note==='R5XSS')`),'준비: B에 공개 기록 수신');
const xid=await B.ev(`S.records.find(r=>r.note==='R5XSS').id`);
ok(await B.ev(`(()=>{const r=S.records.find(r=>r.note==='R5XSS');return !/['"<>]/.test(r.name+r.author)})()`),'2 받은 이름·닉네임에서 따옴표·꺾쇠 제거');
await B.ev(`location.hash='#/detail/${xid}';1`);await sleep(800);await B.ev(`document.querySelector('.species-link')?.click();1`);await sleep(600);
await B.ev(`location.hash='#/home';1`);await sleep(500);
ok(await B.ev(`window.__pwn===undefined`),'2 상세의 종 이름을 눌러도 스크립트 실행 안 됨');
// 정리
for(const id of [srv2])await fetch(`${URL_}api/records/${id}`,{method:'DELETE',headers:{'X-Expert-Key':KEY}});
d1(`DELETE FROM records WHERE note='R5XSS' OR device LIKE 'test-device-%'; UPDATE meta SET v=v+1 WHERE k='version';`);
console.log('errors A:',A.errors.length?A.errors:'none',' B:',B.errors.length?B.errors:'none');procs.forEach(p=>p.kill());process.exit(process.exitCode||0);
