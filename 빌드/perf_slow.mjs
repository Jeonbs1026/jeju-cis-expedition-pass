// 저사양 조건 로딩 측정: CPU 4배 느리게 + 느린 4G. 스크립트별 실행 시간도 수집. 사용: node perf_slow.mjs [주소]
import { spawn } from 'node:child_process';import { mkdtempSync } from 'node:fs';
const URL_=process.argv[2]||'https://jeju-cis.jeju-cis.workers.dev/';const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const p=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9364',`--user-data-dir=${mkdtempSync('/private/tmp/claude-501/cis-perf-')}`,'about:blank']);
let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch('http://127.0.0.1:9364/json')).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
let id=0;const pend={};ws.onmessage=e=>{const m=JSON.parse(e.data);pend[m.id]?.(m)};
const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});
const ev=async x=>(await send('Runtime.evaluate',{expression:x,awaitPromise:true,returnByValue:true})).result.result?.value;
await send('Page.enable');await send('Network.enable');await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:3,mobile:true,screenWidth:390,screenHeight:844});
const runs=[];
for(const [label,cpu,net] of [['기본',1,null],['저사양(CPU×4, 느린 4G)',4,{offline:false,latency:150,downloadThroughput:1.6e6/8,uploadThroughput:750e3/8}]]){
 for(let k=0;k<2;k++){
  // 첫 방문은 캐시를 비우고 시작, 재방문은 바로 앞 방문의 캐시를 그대로 사용
  if(k===0){await send('Network.clearBrowserCache');}await send('Network.setCacheDisabled',{cacheDisabled:false});
  await send('Emulation.setCPUThrottlingRate',{rate:cpu});
  if(net)await send('Network.emulateNetworkConditions',net);else await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});
  await send('Page.navigate',{url:'about:blank'});await sleep(300);
  const t0=Date.now();await send('Page.navigate',{url:URL_+'#/home'});
  let ok=false;for(let i=0;i<1200&&!ok;i++){await sleep(25);ok=await ev(`!!document.querySelector('.home-record-grid .record-card')`)}
  const t=Date.now()-t0;
  const nav=await ev(`JSON.stringify((({responseEnd,domInteractive,domContentLoadedEventEnd})=>({responseEnd:responseEnd|0,domInteractive:domInteractive|0,dcl:domContentLoadedEventEnd|0}))(performance.getEntriesByType('navigation')[0]))`);
  console.log(label,k===0?'첫 방문':'재방문','홈 표시까지',t,'ms',nav);
 }
}
// 지도 화면 진입 시간 (저사양)
const t1=Date.now();await ev(`location.hash='#/map';1`);let ok=false;for(let i=0;i<800&&!ok;i++){await sleep(25);ok=await ev(`!!document.querySelector('.cis-cluster-marker,.cis-static-area')`)}console.log('저사양 지도 표시까지',Date.now()-t1,'ms');
ws.close();p.kill();process.exit(0);
