# 남은 기획 1~5: 전문가 보기=로그인, 오동정 제보 서버 처리, 현재 위치 읍·면·동, 홈 미션 위젯·포인트 애니메이션, 출석·받은 북마크 포인트와 분류·지역·정확도 배지
# 사용: python3 plan_round2.py <JEJU_CIS_최종.html>   (같은 폴더에 .bak)
import sys, shutil

path = sys.argv[1]
shutil.copyfile(path, path + '.bak')
s = open(path, encoding='utf-8').read()
assert 'function pushReports' not in s, '이미 적용됨'

def sub(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, old[:90])
    s = s.replace(old, new)

# ---------- 1. 전문가 보기는 전문가 키 로그인일 때만 ----------
sub("function isExpertView(){return !LEGACY&&S.viewer==='expert'}", "function isExpertView(){return !LEGACY&&SERVER.expert}")
i = s.index("function locationSheet(){"); j = s.index("\n", i)
s = s[:i] + r"""function locationSheet(){sheet('지도 위치 공개 기준',`<p>중간점검에서 정한 기준이에요.</p><div class="sheet-options"><div class="policy-row">${icon('user')}<div><b>일반 회원</b><div class="hint">읍·면·동 단위까지만 보여요.</div></div></div><div class="policy-row">${icon('award')}<div><b>전문가·관리자</b><div class="hint">로그인하면 확대했을 때 정확한 관찰 위치(희귀종 포함)를 볼 수 있어요.</div></div></div></div><p class="hint">지금: <b>${SERVER.expert?'전문가·관리자로 보는 중':'일반 회원으로 보는 중'}</b></p><button class="btn full" onclick="expertLogin()">${EXPERT_KEY?'전문가 로그인 관리':'전문가·관리자 로그인'}</button>`)}""" + s[j:]
sub('<button class="btn outline full" onclick="locationSheet()">보는 사람 바꾸기 (시연)</button>', '<button class="btn outline full" onclick="locationSheet()">위치 공개 기준 보기</button>')
sub("${menuItem('지도 위치 공개 · 시연 계정','map','locationSheet()')}", "${menuItem('지도 위치 공개 기준','map','locationSheet()')}")

# ---------- 2. 오동정 제보: 서버로 보내고 전문가가 반영됨/반영 안 함으로 처리 ----------
sub("제보는 이 브라우저의 시연 데이터에만 저장돼요.", "제보는 전문가·관리자에게 전달되고, 처리 결과는 활동내역과 알림으로 알려 드려요.")
i = s.index("function submitReport(id){"); j = s.index("\n", i)
s = s[:i] + r"""const REPORT_LABEL={pending:'대기 중',accepted:'반영됨',rejected:'반영 안 함','처리 중':'대기 중'};
function submitReport(id){const note=$('#report-note').value.trim();if(!note){toast('제보 내용을 입력해 주세요.');return}const r=S.records.find(x=>x.id===id);S.reports=S.reports||[];S.reports.push({id:Date.now(),record:id,name:r?.name||'관찰 기록',ref:r?.srv?'srv:'+r.srv:'seed:'+id,note,status:'pending',sync:'pending',at:localNow()});save();closeSheet();toast('제보를 보냈어요. 전문가가 확인하면 알려 드릴게요.');syncNow()}""" + s[j:]
sub("async function syncNow(){if(syncBusy)return;syncBusy=true;try{await pushPending();await pull()}",
    r"""async function pushReports(){for(const p of (S.reports||[]).filter(p=>p.sync==='pending')){try{const d=await api('/api/reports',{method:'POST',body:JSON.stringify({device:DEVICE,nickname:nickname(),ref:p.ref,name:p.name,note:p.note})});p.srv=d.srv;p.sync='done';SERVER.pushed=true;save()}catch(e){if(e.status&&e.status<500){p.sync='error';p.syncError=e.message;save()}else return}}}
async function pullReports(){const d=await api('/api/reports?device='+encodeURIComponent(DEVICE));SERVER.reports=d.reports;const by=new Map(d.reports.filter(x=>x.own).map(x=>[x.srv,x]));(S.reports||[]).forEach(p=>{const x=p.srv&&by.get(p.srv);if(!x||(x.status===p.status&&x.reply===(p.reply||'')))return;const prev=p.status;p.status=x.status;p.reply=x.reply;SERVER.pushed=true;if(prev!==x.status&&x.status!=='pending')notifyStatus({id:p.record},x.status==='accepted'?'제보가 반영되었어요':'제보를 검토했어요',x.reply||(x.status==='accepted'?'알려 주신 내용이 기록에 반영되었어요.':'이번에는 반영하지 않기로 했어요.'))})}
async function syncNow(){if(syncBusy)return;syncBusy=true;try{await pushPending();await pushReports();await pullReports();await pull()}""")
sub(r"""(S.reports||[]).map(r=>`<div class="activity-record"><div><span class="badge review">${r.status}</span><h3>${esc(S.records.find(x=>x.id===r.record)?.name||'관찰 기록')}</h3><p>${esc(r.note)}</p><p class="hint">시연 제보 · 실제 기관에 전송되지 않아요.</p></div></div>`).join('')""",
    r"""[...(S.reports||[])].reverse().map(r=>`<div class="activity-record"><div><span class="badge ${r.status==='accepted'?'done':r.status==='rejected'?'unable':'review'}">${REPORT_LABEL[r.status]||'대기 중'}</span><h3>${esc(r.name||S.records.find(x=>x.id===r.record)?.name||'관찰 기록')}</h3><p>${esc(r.note)}</p>${r.reply?`<div class="expert-note"><strong>전문가 답변</strong><p>${esc(r.reply)}</p></div>`:''}<p class="hint">${r.sync==='pending'?'서버 전송 대기 · 연결되면 자동으로 보내요.':r.sync==='error'?'보내지 못했어요: '+esc(r.syncError||''):r.sync==='done'?'전문가·관리자에게 전달됨':'이 기기에만 저장된 예전 제보'}</p></div></div>`).join('')""")
# 전문가 검토 화면에 '오동정 제보' 탭
sub("function review(){if(!SERVER.expert)return `${topbar('전문가 검토')}${empty('전문가·관리자 로그인이 필요해요','운영기관이 발급한 전문가 키로 로그인해 주세요.','expertLogin()','로그인')}`;",
    r"""function reviewTabs(){const n=(SERVER.reports||[]).filter(x=>x.status==='pending').length;return `<div class="tabs"><button class="${state.reviewTab!=='reports'?'active':''}" onclick="state.reviewTab='records';render()">기록 검토</button><button class="${state.reviewTab==='reports'?'active':''}" onclick="state.reviewTab='reports';render()">오동정 제보${n?' '+n:''}</button></div>`}
function reviewReports(){const list=[...(SERVER.reports||[])].sort((a,b)=>(a.status==='pending'?0:1)-(b.status==='pending'?0:1)||b.srv-a.srv);return `${topbar('전문가 검토',`<button class="text-btn" onclick="syncNow().then(render)">새로고침</button>`)}${reviewTabs()}<div class="content" style="padding-bottom:0"><h2 style="font-size:19px">처리 대기 ${list.filter(x=>x.status==='pending').length}건</h2><p class="body-copy">시민이 보낸 잘못된 종 제보예요. 처리 결과는 제보한 사람에게 알림으로 전해져요.</p></div>${list.map(x=>{const rec=x.ref.startsWith('srv:')?S.records.find(r=>r.srv===Number(x.ref.slice(4))):S.records.find(r=>r.id===Number(x.ref.slice(5)));return `<section class="expert-record"><div class="between"><div><h3>${esc(x.name)}</h3><span class="badge ${x.status==='accepted'?'done':x.status==='rejected'?'unable':'review'}">${REPORT_LABEL[x.status]}</span><p class="hint">${esc(x.nickname)} · ${fmt(x.createdAt)}</p></div>${rec?`<button class="text-btn" onclick="openDetail(${rec.id})">기록 보기 ›</button>`:''}</div><p class="body-copy">${esc(x.note)}</p><label class="hint" for="rp-reply-${x.srv}">답변</label><textarea class="field-control" rows="2" id="rp-reply-${x.srv}" placeholder="예: 날개 무늬를 다시 확인해 직박구리로 고쳤어요.">${esc(x.reply||'')}</textarea><div class="review-pub"><button class="btn small" onclick="reportApply(${x.srv},'accepted')">반영됨</button><button class="btn small outline" onclick="reportApply(${x.srv},'rejected')">반영 안 함</button></div></section>`}).join('')||empty('처리할 제보가 없어요','시민이 잘못된 종을 제보하면 여기에 나타나요.',"syncNow().then(render)",'새로고침')}`}
async function reportApply(srv,status){try{await api('/api/reports/'+srv,{method:'PATCH',body:JSON.stringify({status,reply:$(`#rp-reply-${srv}`).value.trim()})});await syncNow();render();toast(status==='accepted'?'반영됨으로 처리했어요.':'반영 안 함으로 처리했어요.')}catch(e){toast(e.message||'서버에 연결할 수 없어요.')}}
function review(){if(!SERVER.expert)return `${topbar('전문가 검토')}${empty('전문가·관리자 로그인이 필요해요','운영기관이 발급한 전문가 키로 로그인해 주세요.','expertLogin()','로그인')}`;if(state.reviewTab==='reports')return reviewReports();""")
sub('<div class="content" style="padding-bottom:0"><div class="eyebrow">EXPERT REVIEW · 서버</div>', '${reviewTabs()}<div class="content" style="padding-bottom:0"><div class="eyebrow">EXPERT REVIEW · 서버</div>')

# ---------- 3. 현재 위치를 읍·면·동 이름으로 (등록 시작 시 바로) ----------
sub("draft.lat=p.coords.latitude;draft.lon=p.coords.longitude;draft.region='현재 위치';render();toast('현재 위치를 불러왔어요. 관찰 위치를 확인해 주세요.')",
    "const lat=p.coords.latitude,lon=p.coords.longitude;if(!(lat>33.1&&lat<33.6&&lon>126.1&&lon<127)){toast('지금 위치가 제주 밖이에요. 지도에서 관찰 위치를 골라 주세요.');return}const nm=window.CISMap?.publicLocation({lat,lon}).name;draft.lat=lat;draft.lon=lon;draft.region=nm||'현재 위치';draft.located=true;render();toast(nm?'현재 위치 · '+nm:'현재 위치를 불러왔어요.')")
sub("draft.lat=meta.latitude;draft.lon=meta.longitude;draft.region='사진 GPS 위치';",
    "draft.lat=meta.latitude;draft.lon=meta.longitude;draft.region=window.CISMap?.publicLocation({lat:meta.latitude,lon:meta.longitude}).name||'사진 GPS 위치';draft.located=true;")
sub("function startRecord(place){resetForm();if(place){draft.lat=place.lat;draft.lon=place.lon;draft.region=place.name;draft.gap=!!place.low}go('register')}",
    "function startRecord(place){resetForm();if(place){draft.lat=place.lat;draft.lon=place.lon;draft.region=place.name;draft.gap=!!place.low;draft.located=true}go('register');if(!place&&!LEGACY)autoLocate()}\n"
    "// 위치 권한을 이미 허용했으면 등록을 시작할 때 바로 현재 위치(읍·면·동)로 채움. 아니면 화면의 안내 버튼으로 요청\n"
    "function autoLocate(){navigator.permissions?.query({name:'geolocation'}).then(p=>{if(p.state==='granted'&&route==='register'&&draft&&!draft.located)requestLocation()}).catch(()=>{})}")
sub('<div id="register-map" class="register-map"></div>',
    r"""${!LEGACY&&!draft.id&&!draft.located?`<button class="locate-banner" onclick="requestLocation()">${icon('target')}<span><b>지금 있는 곳으로 시작할까요?</b>현재 위치를 읍·면·동으로 바로 채워요</span></button>`:''}<div id="register-map" class="register-map"></div>""")

# ---------- 4. 홈 주간 미션 위젯, 포인트 적립 애니메이션 ----------
sub('</section><div class="home-filter">', "</section>${LEGACY?'':homeMission()}<div class=\"home-filter\">")
sub("function homeCard(r){",
    r"""function homeMission(){const list=missionItems(),done=list.filter(m=>m.cur>=m.goal).length,next=list.find(m=>m.cur<m.goal);return `<button class="home-mission" onclick="go('missions')"><span class="hm-top"><span class="eyebrow">이번 주 탐사 미션</span><b>${done} / ${list.length} ›</b></span><span class="progress-track"><i style="width:${done/list.length*100}%"></i></span><span class="hm-next">${next?'다음 · '+esc(next.name)+' ('+Math.min(next.cur,next.goal)+'/'+next.goal+')':'이번 주 미션을 모두 달성했어요!'}</span></button>`}
function homeCard(r){""")
sub("${gain&&!LEGACY?`<div class=\"earned\">+${gain}P${nb.length?' · 새 배지 '+nb.join(', '):''}</div>`:''}",
    "${gain&&!LEGACY?`<div class=\"earned\">+<span class=\"earn-num\">${gain}</span>P${nb.length?' · 새 배지 '+nb.join(', '):''}</div>`:''}")
sub("동정 결과 알림 설정</button>`:''}</div>`),80)}", "동정 결과 알림 설정</button>`:''}</div>`);animateEarn()},80)}")
sub("go('detail',r.id);syncNow();setTimeout(()=>sheet('관찰을 기록했어요',", "go('detail',r.id);syncNow();setTimeout(()=>{sheet('관찰을 기록했어요',")
sub("function homeMission(){",
    "function animateEarn(){const el=$('.sheet .earn-num');if(!el)return;el.closest('.earned').classList.add('pop');if(matchMedia('(prefers-reduced-motion: reduce)').matches)return;const end=Number(el.textContent),t0=performance.now(),step=t=>{const k=Math.min(1,(t-t0)/700);el.textContent=Math.round(end*(1-(1-k)**3));if(k<1)requestAnimationFrame(step)};el.textContent='0';requestAnimationFrame(step)}\n"
    "function homeMission(){")

# ---------- 5. 출석·받은 북마크 포인트, 분류·지역·정확도 배지, 기기 간 북마크 ----------
sub("const POINTS={record:10,complete:5,gap:15,done:20,first:50,mission:30};",
    "const POINTS={record:10,complete:5,gap:15,done:20,first:50,mission:30,attend:2,streak3:10,streak7:30,liked:1};\n"
    "// 출석: 앱을 연 날마다 +2, 3일·7일 연속이면 보너스. 받은 북마크: 기록당 최대 20개까지 1P\n"
    "function markVisit(){const d=localNow().slice(0,10);S.visits=S.visits||[];if(!S.visits.includes(d)){S.visits=[...S.visits,d].slice(-60);save()}}\n"
    "function attendLog(){const days=[...new Set(S.visits||[])].sort(),log=[];let run=0,prev=null;days.forEach(d=>{run=prev&&Date.parse(d)-Date.parse(prev)===864e5?run+1:1;prev=d;log.push({label:'출석 · '+d.slice(5).replace('-','.'),p:POINTS.attend,at:d+'T09:00'});if(run===3)log.push({label:'3일 연속 출석',p:POINTS.streak3,at:d+'T09:00'});if(run===7)log.push({label:'7일 연속 출석',p:POINTS.streak7,at:d+'T09:00'})});return log}")
sub("if(first)add('제주 첫 기록 · '+r.name,POINTS.first)});if(author===ME)missionItems()",
    "if(first)add('제주 첫 기록 · '+r.name,POINTS.first);const liked=Math.min(r.bookmarks||0,20);if(liked)add('받은 북마크 · '+r.name,liked*POINTS.liked)});if(author===ME)log.push(...attendLog());if(author===ME)missionItems()")
sub("['제주 첫 기록','trophy',pointLog().some(x=>x.label.startsWith('제주 첫'))]]}",
    "['제주 첫 기록','trophy',pointLog().some(x=>x.label.startsWith('제주 첫'))],['새 관찰가','bird',m.filter(r=>r.taxon==='bird').length>=3],['식물 관찰가','plant',m.filter(r=>r.taxon==='plant').length>=3],['곤충 관찰가','insect',m.filter(r=>r.taxon==='insect').length>=3],['제주시 탐험가','map',cityAreas(m,'제주시')>=3],['서귀포시 탐험가','map',cityAreas(m,'서귀포시')>=3],['정확한 관찰가','target',m.filter(r=>r.status==='done').length>=3]]}\n"
    "function cityAreas(m,city){return new Set(m.map(regionName).filter(n=>n.startsWith(city))).size}")
sub("'제주 첫 기록':['제주에서 처음 동정 완료된 종 기록',()=>[pointLog().some(x=>x.label.startsWith('제주 첫'))?1:0,1]]};",
    "'제주 첫 기록':['제주에서 처음 동정 완료된 종 기록',()=>[pointLog().some(x=>x.label.startsWith('제주 첫'))?1:0,1]],'새 관찰가':['조류 기록 3건',m=>[m.filter(r=>r.taxon==='bird').length,3]],'식물 관찰가':['육상식물 기록 3건',m=>[m.filter(r=>r.taxon==='plant').length,3]],'곤충 관찰가':['곤충 기록 3건',m=>[m.filter(r=>r.taxon==='insect').length,3]],'제주시 탐험가':['제주시의 읍·면·동 3곳에서 기록',m=>[cityAreas(m,'제주시'),3]],'서귀포시 탐험가':['서귀포시의 읍·면·동 3곳에서 기록',m=>[cityAreas(m,'서귀포시'),3]],'정확한 관찰가':['전문가 동정이 완료된 기록 3건',m=>[m.filter(r=>r.status==='done').length,3]]};")
# 북마크를 서버와 맞춤 (공개 기록·내 서버 기록)
sub("function toggleBookmark(id,el){id=Number(id);if(saved(id))S.saved=S.saved.filter(v=>v!==id);else S.saved.push(id);save();",
    "function toggleBookmark(id,el){id=Number(id);if(saved(id))S.saved=S.saved.filter(v=>v!==id);else S.saved.push(id);save();const br=S.records.find(r=>r.id===id);if(br?.srv&&(br.remote||br.sync==='done'))api('/api/records/'+br.srv+'/bookmark',{method:'POST',body:JSON.stringify({device:DEVICE,on:saved(id)})}).catch(()=>{});")
sub("bookmarks:0,views:x.views,gap:x.gap,public:x.public}}", "bookmarks:x.bookmarks||0,views:x.views,gap:x.gap,public:x.public}}")
sub("  if(x.views!==r.views)r.views=x.views});", "  if(x.views!==r.views)r.views=x.views;if((x.bookmarks||0)!==(r.bookmarks||0)){r.bookmarks=x.bookmarks||0;changed=true}});")
sub(" const remote=d.records.filter(x=>!x.own&&x.public===1).map(fromServer),",
    " d.records.forEach(x=>{if(x.own||x.public!==1)return;const sid=SRV_ID+x.srv,has=S.saved.includes(sid);if(x.bookmarked&&!has)S.saved.push(sid);if(!x.bookmarked&&has)S.saved=S.saved.filter(v=>v!==sid)});\n const remote=d.records.filter(x=>!x.own&&x.public===1).map(fromServer),")
sub("remote.map(x=>x.srv+x.status+x.name).join()", "remote.map(x=>x.srv+x.status+x.name+x.bookmarks).join()")
# 출석 기록: 시작할 때와 시연 초기화 때
sub("reset(){S=seed();save();render()}", "reset(){S=seed();markVisit();save();render()}")
sub("syncMode();render();startSync();}", "syncMode();markVisit();render();startSync();}")

sub('.cis-legacy-pin svg{', """.policy-row{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid var(--line);font-size:13px}.policy-row .icon{width:20px;height:20px;color:var(--green);flex:none}
.locate-banner{display:flex;gap:10px;align-items:center;width:100%;margin:6px 0 10px;padding:12px 14px;border:1px solid #cfe8dd;border-radius:14px;background:#f2faf6;text-align:left;font:inherit;color:var(--deep);cursor:pointer}.locate-banner .icon{width:20px;height:20px;flex:none}.locate-banner span{display:flex;flex-direction:column;font-size:11px;color:#5f7a6e}.locate-banner b{font-size:13px;color:var(--deep)}
.home-mission{display:block;width:calc(100% - 10cqw);margin:3cqw 5cqw 0;padding:14px 16px;border:1px solid #d9ebe3;border-radius:16px;background:#f3faf7;text-align:left;font:inherit;color:var(--text);cursor:pointer}.home-mission .hm-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}.home-mission .hm-top b{font-size:13px;color:var(--deep)}.home-mission .progress-track{display:block}.home-mission .hm-next{display:block;margin-top:8px;font-size:12px;color:#5f6f68}
.earned.pop{animation:earnPop .6s cubic-bezier(.2,1.4,.4,1)}@keyframes earnPop{0%{transform:scale(.6);opacity:0}100%{transform:none;opacity:1}}@media (prefers-reduced-motion:reduce){.earned.pop{animation:none}}
.cis-legacy-pin svg{""")

open(path, 'w', encoding='utf-8').write(s)
print('ok', path)
