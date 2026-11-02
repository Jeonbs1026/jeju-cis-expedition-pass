// 라운드7 점검: 전문가 검토 화면에서 승인 전·비공개 사진 흐림, 누르면 보임. 사용: node e2e_round6.mjs <앱 URL>
import { spawn } from 'node:child_process';import { mkdtempSync } from 'node:fs';
const url=process.argv[2];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const p=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9357',`--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-r7-')}`,'about:blank']);
let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch('http://127.0.0.1:9357/json')).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
let id=0;const pend={};ws.onmessage=e=>{const m=JSON.parse(e.data);pend[m.id]?.(m)};
const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});
const ev=async x=>(await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true})).result.result?.value;
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
await send('Page.navigate',{url:url+'#/register'});await sleep(3000);
let pass=0,fail=0;const ok=(c,m)=>{c?pass++:fail++;console.log(c?'✓':'✗',m)};
const r=await ev(`(()=>{setLegacy(false);SERVER.expert=true;const b={name:'테스트',nickname:'t',region:'',at:'2026-11-02T10:00',lat:33.4,lon:126.5,status:'requested',updatedAt:''};SERVER.list=[{...b,srv:1,public:0},{...b,srv:2,public:1},{...b,srv:3,public:-1}];const app=document.querySelector('#app');app.innerHTML=review();const imgs=[...app.querySelectorAll('.review-record img')];const before=imgs.map(i=>i.classList.contains('blur-photo'));imgs.find(i=>i.classList.contains('blur-photo')).click();app.innerHTML=review();const after=[...app.querySelectorAll('.review-record img')].map(i=>i.classList.contains('blur-photo'));return {before,after,hint:app.querySelectorAll('.blur-hint').length}})()`);
console.log(JSON.stringify(r));
const bl=o=>r.before[o];ok(r.before.filter(Boolean).length===2&&r.before.length===3,'승인 전·비공개 2장 흐림, 공개 1장은 그대로');
ok(r.after.filter(Boolean).length===1,'누른 사진은 다시 그려도 계속 보임');
console.log(`${pass}/${pass+fail}`);ws.close();p.kill();process.exit(fail?1:0);
