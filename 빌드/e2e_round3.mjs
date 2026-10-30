// 라운드3 검사: 내 주변 크게 표시, 안내 문구. 사용: node e2e_round3.mjs [주소] [스크린샷경로]
import { spawn } from 'node:child_process';import { mkdtempSync, writeFileSync } from 'node:fs';
const URL_=process.argv[2]||'https://jeju-cis.jeju-cis.workers.dev/',SHOT=process.argv[3];const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const ok=(c,m)=>{console.log(c?'PASS':'FAIL',m);if(!c)process.exitCode=1};
const p=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9363',`--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-r3-')}`,'about:blank']);
let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch('http://127.0.0.1:9363/json')).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
let id=0;const pend={},errors=[];ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.exception?.description?.split('\n')[0]);pend[m.id]?.(m)};
const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});
const ev=async x=>(await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true})).result.result?.value;
await send('Runtime.enable');await send('Page.enable');await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:2,mobile:true,screenWidth:390,screenHeight:844});
await send('Browser.grantPermissions',{permissions:['geolocation'],origin:new URL(URL_).origin});await send('Emulation.setGeolocationOverride',{latitude:33.4565,longitude:126.5615,accuracy:20});
await send('Page.navigate',{url:URL_+'#/home'});await sleep(3500);
ok(await ev(`document.title.indexOf('v3')<0&&!/v3/.test(document.querySelector('.home-footer')?.textContent)`),'v3 표기 없음');
await ev(`setLegacy(false);state.mode='eco';location.hash='#/map';1`);await sleep(3500);
ok(await ev(`!!state.near`),'권한 있으면 지도 열 때 내 주변 자동');
ok(await ev(`document.querySelectorAll('.cis-cluster-marker.is-near').length>0&&!!document.querySelector('.cis-me')`),'내 주변 지역 원 크게 + 내 위치 점 ('+await ev(`[...document.querySelectorAll('.cis-cluster-marker.is-near')].map(e=>e.dataset.area).join(',')`)+')');
if(SHOT)writeFileSync(SHOT,Buffer.from((await send('Page.captureScreenshot',{format:'png'})).result.data,'base64'));
await ev(`document.querySelector('.near-btn').click();1`);await sleep(2500);ok(await ev(`!state.near&&!document.querySelector('.cis-cluster-marker.is-near')`),'다시 누르면 끔');
await send('Emulation.setGeolocationOverride',{latitude:37.5665,longitude:126.978,accuracy:20});await ev(`nearMe();1`);await sleep(1500);ok(await ev(`!state.near&&/제주 밖/.test(document.querySelector('#toast').textContent)`),'제주 밖이면 켜지 않음');
await ev(`setLegacy(true);1`);await sleep(2500);ok(await ev(`!document.querySelector('.near-btn')`),'기존 모드에서는 버튼 없음');
await ev(`setLegacy(false);location.hash='#/faq';1`);await sleep(500);ok(await ev(`/시연용 서버/.test(document.querySelector('.faq-list').textContent)`),'FAQ 저장 안내 갱신');
console.log('오류',errors.length?errors:'없음');ws.close();p.kill();process.exit(process.exitCode||0);
