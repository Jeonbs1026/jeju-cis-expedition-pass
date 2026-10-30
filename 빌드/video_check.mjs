// 시연 영상 점검: 녹화 모드로 끝까지 재생, 주기적 스크린샷, 못 찾은 요소·오류·총 길이. 사용: node video_check.mjs <영상.html 절대경로> <스크린샷 폴더>
import { spawn } from 'node:child_process';import { mkdtempSync, writeFileSync, mkdirSync } from 'node:fs';
const [html,out]=process.argv.slice(2);mkdirSync(out,{recursive:true});const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const p=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9372',`--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-vid-')}`,'about:blank']);
let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch('http://127.0.0.1:9372/json')).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
let id=0;const pend={},log=[];ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')log.push('ERR '+m.params.exceptionDetails.exception?.description?.split('\n')[0]);if(m.method==='Runtime.consoleAPICalled'&&['warning','error'].includes(m.params.type))log.push(m.params.type+' '+m.params.args.map(a=>a.value||a.description).join(' ').slice(0,120));pend[m.id]?.(m)};
const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});const ev=async x=>(await send('Runtime.evaluate',{expression:x,returnByValue:true})).result.result?.value;
await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:1600,height:900,deviceScaleFactor:1,mobile:false});
await send('Page.navigate',{url:'file://'+html+'?record'});const t0=Date.now();let k=0;
while(!(await ev('!!window.__done'))&&Date.now()-t0<240000){await sleep(6000);k++;writeFileSync(`${out}/v${String(k).padStart(3,'0')}.png`,Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'))}
console.log('총 길이',Math.round((Date.now()-t0)/1000),'초 (로딩 포함) · 스크린샷',k,'장');console.log(log.length?log.join('\n'):'경고·오류 없음');ws.close();p.kill();process.exit(0);
