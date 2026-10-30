// 시연 영상 HTML을 녹화해 MP4로 저장 (헤드리스 Chrome 화면 캡처 + ffmpeg)
// 사용: node video_record.mjs <영상.html 절대경로> <출력.mp4> <ffmpeg 경로>
import { spawn, execFileSync } from 'node:child_process';import { mkdtempSync, writeFileSync } from 'node:fs';
const [html,outMp4,FFMPEG]=process.argv.slice(2);const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const dir=mkdtempSync('/private/tmp/claude-501/cis-rec-');
const p=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',['--headless=new','--remote-debugging-port=9373',`--user-data-dir=${dir}/profile`,'--hide-scrollbars','about:blank']);
let ws;for(let i=0;i<50&&!ws;i++){await sleep(300);try{const t=(await (await fetch('http://127.0.0.1:9373/json')).json()).find(t=>t.type==='page');ws=new WebSocket(t.webSocketDebuggerUrl);await new Promise((a,b)=>{ws.onopen=a;ws.onerror=b})}catch{ws=null}}
let id=0;const pend={},frames=[];
ws.onmessage=e=>{const m=JSON.parse(e.data);
 if(m.method==='Page.screencastFrame'){const f=`${dir}/f${String(frames.length).padStart(5,'0')}.jpg`;writeFileSync(f,Buffer.from(m.params.data,'base64'));frames.push({f,t:m.params.metadata.timestamp});ws.send(JSON.stringify({id:++id,method:'Page.screencastFrameAck',params:{sessionId:m.params.sessionId}}))}
 pend[m.id]?.(m)};
const send=(method,params={})=>new Promise(r=>{pend[++id]=r;ws.send(JSON.stringify({id,method,params}))});const ev=async x=>(await send('Runtime.evaluate',{expression:x,returnByValue:true})).result.result?.value;
await send('Page.enable');await send('Runtime.enable');await send('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
// 앱을 미리 불러온 뒤 녹화 시작 (녹화 모드는 불러오면 자동 재생)
await send('Page.navigate',{url:'file://'+html+'?record'});
for(let i=0;i<200&&!(await ev('!!window.__ready'));i++)await sleep(100);
await send('Page.startScreencast',{format:'jpeg',quality:92,maxWidth:1920,maxHeight:1080,everyNthFrame:1});
const t0=Date.now();while(!(await ev('!!window.__done'))&&Date.now()-t0<240000)await sleep(500);
await sleep(800);await send('Page.stopScreencast');ws.close();p.kill();
// 프레임마다 화면에 머문 시간으로 이어 붙이기
let list='';for(let i=0;i<frames.length;i++){const d=i<frames.length-1?Math.max(0.001,frames[i+1].t-frames[i].t):0.5;list+=`file '${frames[i].f}'\nduration ${d.toFixed(4)}\n`}
list+=`file '${frames.at(-1).f}'\n`;writeFileSync(`${dir}/list.txt`,list);
const total=frames.at(-1).t-frames[0].t;console.log('프레임',frames.length,'장 · 길이',total.toFixed(1),'초');
execFileSync(FFMPEG,['-y','-loglevel','error','-f','concat','-safe','0','-i',`${dir}/list.txt`,'-vf','fps=30,scale=1920:1080:flags=lanczos,format=yuv420p','-c:v','libx264','-preset','medium','-crf','20','-movflags','+faststart',outMp4],{stdio:'inherit'});
console.log('저장',outMp4);process.exit(0);
