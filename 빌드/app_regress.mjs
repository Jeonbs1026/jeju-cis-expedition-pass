// 앱 회귀 점검: 모든 화면을 기존·개선 모드로 열고 오류 수집 (전문가 키가 있으면 검토 화면까지)
import { spawn } from 'node:child_process';import { mkdtempSync } from 'node:fs';
const [url,key]=process.argv.slice(2);const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const p=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9354',`--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-reg-')}`,'about:blank']);
let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch('http://127.0.0.1:9354/json')).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
let id=0;const pend={},errors=[];ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description?.split('\n')[0]);pend[m.id]?.(m)};
const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});
const ev=async x=>(await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true})).result.result?.value;
await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true,screenWidth:390,screenHeight:844});
await send('Page.navigate',{url:url+'#/home'});await sleep(4000);
const routes=['home','archive','detail/1','detail/3','about','columns','article','guide','gallery','my','report','grade','points','badges','ranking','missions','activity','notifications','menu','profile','settings','map','register','expert','faq','inquiries','notices','resources','interests','review'];
let empty=0;for(const L of [false,true]){await ev(`setLegacy(${L});1`);for(const r of routes){await ev(`location.hash='#/${r}';1`);await sleep(r==='map'||r==='register'?1500:350);if(!(await ev(`document.querySelector('#app').innerHTML.length>200`))){empty++;console.log('빈 화면',L?'기존':'개선',r)}}}
if(key){await ev(`setLegacy(false);expertLogin();document.querySelector('#expert-key').value='${key}';saveExpertKey()`);await sleep(3000);console.log('전문가 검토 화면:',await ev(`location.hash+' '+(document.querySelector('#app h2')?.textContent||'')`));await ev(`saveExpertKey(true)`);await sleep(1500)}
console.log('화면',routes.length*2,'· 빈 화면',empty,'· 오류',errors.length?errors:'없음');ws.close();p.kill();process.exit(0);
