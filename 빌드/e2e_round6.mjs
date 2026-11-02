// 라운드6 점검: 같은 화면 다시 그리기 시 스크롤 유지, 화면 이동 시 맨 위, 삭제 확인 시트. 사용: node e2e_round6.mjs <앱 URL>
import { spawn } from 'node:child_process';import { mkdtempSync } from 'node:fs';
const url=process.argv[2];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const p=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9356',`--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-r6-')}`,'about:blank']);
let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch('http://127.0.0.1:9356/json')).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
let id=0;const pend={};ws.onmessage=e=>{const m=JSON.parse(e.data);pend[m.id]?.(m)};
const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});
const ev=async x=>(await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true})).result.result?.value;
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
await send('Page.navigate',{url:url+'#/register'});await sleep(3000);
let pass=0,fail=0;const ok=(c,m)=>{c?pass++:fail++;console.log(c?'✓':'✗',m)};
await ev(`setLegacy(false);location.hash='#/register';1`);await sleep(1500);
await ev(`window.scrollTo(0,400);1`);await sleep(200);const y0=await ev('scrollY');
await ev(`render();1`);await sleep(800);ok(y0>0&&await ev('scrollY')===y0,`같은 화면 다시 그리기: 스크롤 ${y0} 유지`);
await ev(`location.hash='#/archive';1`);await sleep(800);ok(await ev('scrollY')===0,'다른 화면으로 이동하면 맨 위');
await ev(`reviewDelete(999999);1`);await sleep(300);ok(await ev(`!!document.querySelector('#overlay .sheet')&&document.querySelector('#sheet-title').textContent.includes('삭제')`),'삭제 누르면 확인 시트');
console.log(`${pass}/${pass+fail}`);ws.close();p.kill();process.exit(fail?1:0);
