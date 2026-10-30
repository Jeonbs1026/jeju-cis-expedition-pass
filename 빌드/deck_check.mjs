// 발표 덱 점검: 모든 슬라이드 넘김, 시연 슬라이드에서 내장 앱이 기존 모드·해당 화면으로 열리는지, 오류 수집
import { spawn } from 'node:child_process';import { mkdtempSync } from 'node:fs';
const deck=process.argv[2];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const p=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9353',`--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-deck-')}`,'about:blank']);
let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch('http://127.0.0.1:9353/json')).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
let id=0;const pend={},errors=[];ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description?.split('\n')[0]);pend[m.id]?.(m)};
const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});
const ev=async x=>(await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true})).result.result?.value;
await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:1600,height:900,deviceScaleFactor:1,mobile:false});
await send('Page.navigate',{url:'file://'+deck});await sleep(6000);
const n=await ev('document.querySelectorAll(".slide").length');let bad=0;
for(let k=0;k<n;k++){await ev(`presentationGo(${k});1`);await sleep(1500);if(process.argv[3])require_shot:{const f=process.argv[3]+'/slide'+String(k+1).padStart(2,'0')+'.png';(await import('node:fs')).writeFileSync(f,Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'))}const s=await ev(`(()=>{const sl=document.querySelectorAll('.slide')[${k}],w=document.getElementById('app').contentWindow;return sl.dataset.app?{want:sl.dataset.app,wantLegacy:sl.dataset.legacy==='1',hash:w.location.hash,legacy:w.document.documentElement.classList.contains('legacy')}:null})()`);
 if(s){const good=s.hash==='#/'+s.want&&s.legacy===s.wantLegacy;if(!good)bad++;console.log(k+1,good?'OK':'BAD',JSON.stringify(s))}}
console.log(n,'slides · 시연 슬라이드 문제',bad,'· 오류',errors.length?errors:'없음');ws.close();p.kill();process.exit(0);
