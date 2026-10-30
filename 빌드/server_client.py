# 최종 앱에 서버 연동 추가 (검수 후 공개 · 전문가 동정 실연 · 오프라인 임시저장)
# 사용: python3 server_client.py <JEJU_CIS_최종.html>   (제자리 수정, 같은 디렉터리에 .bak 남김)
import sys, shutil

path = sys.argv[1]
shutil.copyfile(path, path + '.bak')
s = open(path, encoding='utf-8').read()
assert 'const API=' not in s, '이미 적용됨'

def sub(old, new):
    global s
    n = s.count(old)
    assert n == 1, (n, old[:80])
    s = s.replace(old, new)

# ---- 저장: 다른 사람의 공개 기록(remote)은 기기에 저장하지 않음 ----
sub("function save(){try{localStorage.setItem(KEY,JSON.stringify(S));return true}",
    "function save(){try{localStorage.setItem(KEY,JSON.stringify({...S,records:S.records.filter(r=>!r.remote)}));return true}")

# ---- 서버 연동 모듈 ----
sub("function imageSrc(r){return r.photo?.startsWith('data:')?r.photo:",
    r"""// 서버 연동: 내 기록은 기기에 먼저 저장 → 서버로 전송(실패하면 대기 후 재시도). 남의 기록은 전문가가 공개 승인한 것만 받음
const API=location.protocol.startsWith('http')?'':'https://jeju-cis.jeju-cis.workers.dev',SRV_ID=9e12;
const DEVICE=(()=>{try{let d=localStorage.getItem('jeju-cis-device');if(!d){d='d-'+(crypto.randomUUID?.()||Math.random().toString(36).slice(2)+Date.now().toString(36));localStorage.setItem('jeju-cis-device',d)}return d}catch{return 'd-'+Math.random().toString(36).slice(2)+Date.now().toString(36)}})();
let EXPERT_KEY='',SERVER={ok:null,expert:false,list:[],sig:''},syncBusy=false;try{EXPERT_KEY=localStorage.getItem('jeju-cis-expert-key')||''}catch{}
function nickname(){if(!S.nickname){S.nickname='탐험가'+(1000+Math.floor(Math.random()*9000));save()}return S.nickname}
async function api(path,opt={}){const r=await fetch(API+path,{...opt,headers:{'Content-Type':'application/json',...(EXPERT_KEY?{'X-Expert-Key':EXPERT_KEY}:{})}});const d=await r.json().catch(()=>({}));if(!r.ok)throw Object.assign(new Error(d.error||('HTTP '+r.status)),{status:r.status});return d}
function photoData(r){return r.photo?.startsWith('data:image/jpeg')?r.photo:window.__CIS_ASSETS?.[r.photo]||''}
function photoUrl(x){return API+'/api/photo/'+x.srv+'?device='+encodeURIComponent(DEVICE)+(SERVER.expert&&EXPERT_KEY?'&k='+encodeURIComponent(EXPERT_KEY):'')+'&v='+encodeURIComponent(x.updatedAt||'')}
function fromServer(x){return {id:SRV_ID+x.srv,srv:x.srv,remote:true,author:x.nickname===ME?x.nickname+'·':x.nickname,photo:photoUrl(x),taxon:x.taxon,name:x.name,nameLevel:x.nameLevel,scientific:x.scientific,status:x.status,lat:x.lat,lon:x.lon,region:x.region,at:x.at,createdAt:x.createdAt,note:x.note,expertNote:x.expertNote,bookmarks:0,views:x.views,gap:x.gap,public:x.public}}
async function pushPending(){for(const r of S.records.filter(r=>r.author===ME&&r.sync==='pending')){const body={device:DEVICE,nickname:nickname(),record:{taxon:r.taxon,name:r.name,nameLevel:r.nameLevel||'species',scientific:r.scientific||'',status:r.status==='requested'?'requested':'recorded',lat:r.lat,lon:r.lon,region:r.region||'',at:r.at,note:r.note||'',photo:photoData(r),gap:!!r.gap}};
 try{const d=r.srv?await api('/api/records/'+r.srv,{method:'PUT',body:JSON.stringify(body)}):await api('/api/records',{method:'POST',body:JSON.stringify(body)});r.srv=d.record.srv;r.sync='done';r.public=d.record.public;r.syncError='';SERVER.pushed=true;SERVER.dirty=true;save();refreshIfSafe();toast('서버에 기록을 올렸어요. 전문가 확인 후 공개돼요.')}
 catch(e){if(e.status&&e.status<500){r.sync='error';r.syncError=e.message;save();toast('서버에 올리지 못했어요: '+e.message)}else{SERVER.ok=false;return}}}}
function notifyStatus(r,title,body){S.notifications.unshift({id:Date.now()+Math.random(),record:r.id,title,body,at:fmt(localNow()),read:false});toast(title);if(S.notificationOptIn&&'Notification'in window&&Notification.permission==='granted'){try{new Notification(title,{body,icon:window.__CIS_ASSETS['logo.png']})}catch{}}}
async function pull(){const d=await api('/api/records?device='+encodeURIComponent(DEVICE));SERVER.ok=true;SERVER.expert=!!d.expert;SERVER.list=d.records;let changed=false;const own=new Map(d.records.filter(x=>x.own).map(x=>[x.srv,x]));
 S.records.forEach(r=>{const x=r.author===ME&&r.srv&&r.sync==='done'&&own.get(r.srv);if(!x)return;if(x.status!==r.status||x.expertNote!==(r.expertNote||'')||x.public!==r.public||x.name!==r.name){const prev=r.status,prevPub=r.public;Object.assign(r,{status:x.status,expertNote:x.expertNote,name:x.name,scientific:x.scientific,taxon:x.taxon,nameLevel:x.nameLevel,public:x.public});changed=true;
  if(prev!==x.status){const t={review:'전문가가 기록을 살펴보고 있어요',done:'생물의 이름을 확인했어요',unable:'추가 사진이 필요해요'}[x.status];if(t)notifyStatus(r,t,x.status==='done'?`${x.name}로 동정이 완료되었어요.`:x.expertNote||'')}
  if(prevPub!==x.public&&x.public===1)notifyStatus(r,'기록이 공개되었어요','전문가가 확인해 다른 사람도 볼 수 있어요.');if(prevPub!==x.public&&x.public===-1)notifyStatus(r,'기록이 비공개로 처리되었어요','전문가 의견을 확인해 주세요.')}
  if(x.views!==r.views)r.views=x.views});
 const remote=d.records.filter(x=>!x.own&&x.public===1).map(fromServer),sig=remote.map(x=>x.srv+x.status+x.name).join()+'|'+(SERVER.expert?d.records.map(x=>x.srv+x.status+x.public).join():'');
 if(sig!==SERVER.sig){SERVER.sig=sig;S.records=[...S.records.filter(r=>!r.remote),...remote];changed=true}
 if(changed||SERVER.pushed){SERVER.pushed=false;save();SERVER.dirty=true;refreshIfSafe()}}
// 화면 갱신은 시트·입력 중이 아닐 때만. 미뤄 둔 갱신은 시트를 닫을 때 처리
function refreshIfSafe(){if(SERVER.dirty&&!$('.sheet')&&route!=='register'&&!document.activeElement?.matches?.('input,textarea,select')){SERVER.dirty=false;render()}}
async function syncNow(){if(syncBusy)return;syncBusy=true;try{await pushPending();await pull()}catch{SERVER.ok=false}finally{syncBusy=false}}
function startSync(){syncNow();setInterval(()=>{if(document.visibilityState==='visible')syncNow()},12000);addEventListener('online',syncNow);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')syncNow()})}
function syncLine(r){if(LEGACY||r.author!==ME||!r.sync)return '';const t=r.sync==='pending'?['wait','서버 전송 대기','연결되면 자동으로 올라가요.']:r.sync==='error'?['err','서버 전송 실패',r.syncError||'']:r.public===1?['pub','공개됨','다른 사람도 볼 수 있어요.']:r.public===-1?['hid','비공개 처리','전문가가 공개하지 않기로 했어요.']:['rev','공개 검토 중','전문가가 확인한 뒤 다른 사람에게 보여요.'];return `<div class="sync-line sync-${t[0]}"><b>${t[1]}</b><span>${esc(t[2])}</span></div>`}
function imageSrc(r){return r.photo?.startsWith('data:')||r.remote?r.photo:""")

# ---- 등록: 기기에 저장한 뒤 전송 대기열에 ----
sub("bookmarks:draft.bookmarks||0,views:draft.views||0,expertNote:'',gap:draft.gap};",
    "bookmarks:draft.bookmarks||0,views:draft.views||0,expertNote:'',gap:draft.gap,srv:draft.srv,sync:'pending',public:0};")
sub("go('detail',r.id);setTimeout(()=>sheet('관찰을 기록했어요',",
    "go('detail',r.id);syncNow();setTimeout(()=>sheet('관찰을 기록했어요',")
sub("'내 관찰 기록에 저장했어요.<br>오늘의 작은 발견이 제주의 기록이 됩니다.'}</p>",
    "'내 관찰 기록에 저장했어요.<br>오늘의 작은 발견이 제주의 기록이 됩니다.'}</p>${LEGACY?'':'<p class=\"hint\">사진과 기록은 전문가가 확인한 뒤에 다른 사람에게 공개돼요.</p>'}")

# ---- 상세: 공개 상태 표시, 남의 공개 기록 조회수는 서버로 ----
sub("if(r&&!SEEN.has(r.id)){SEEN.add(r.id);r.views=viewsOf(r)+1;",
    "if(r&&!SEEN.has(r.id)){SEEN.add(r.id);if(r.remote)api('/api/records/'+r.srv+'/view',{method:'POST',body:JSON.stringify({device:DEVICE})}).catch(()=>{});r.views=viewsOf(r)+1;")
sub("<span class=\"date\">${fmt(r.at)}</span></div>${LEGACY?'':statusTimeline(r)}",
    "<span class=\"date\">${fmt(r.at)}</span></div>${syncLine(r)}${LEGACY?'':statusTimeline(r)}")

# ---- 삭제: 서버에 올라간 기록은 서버에서도 삭제 ----
sub("function confirmDelete(id){const r=S.records.find(x=>x.id===id);if(!r||r.author!==ME||r.status==='done')return;S.records=S.records.filter(x=>x.id!==id);",
    "async function confirmDelete(id){const r=S.records.find(x=>x.id===id);if(!r||r.author!==ME||r.status==='done')return;if(r.srv){try{await api('/api/records/'+r.srv+'?device='+encodeURIComponent(DEVICE),{method:'DELETE'})}catch(e){if(e.status!==404){toast(e.status?e.message:'인터넷에 연결되면 다시 삭제해 주세요.');closeSheet();return}}}S.records=S.records.filter(x=>x.id!==id);")

# ---- 전문가·관리자: 키 로그인과 서버 검토 화면 ----
sub("function expert(){", r"""function expertLogin(){sheet('전문가·관리자 로그인',`<p>운영기관이 발급한 전문가 키로 로그인하면, 시민이 올린 기록을 검토해 동정하고 공개 여부를 정할 수 있어요.</p><label class="field-label" for="expert-key">전문가 키</label><input class="field-control" id="expert-key" type="password" autocomplete="off" value="${esc(EXPERT_KEY)}"><button class="btn full space-top" onclick="saveExpertKey()">로그인</button>${EXPERT_KEY?'<button class="btn outline full" onclick="saveExpertKey(true)">로그아웃</button>':''}`)}
async function saveExpertKey(out){const k=out?'':$('#expert-key').value.trim();EXPERT_KEY=k;try{localStorage.setItem('jeju-cis-expert-key',k)}catch{}if(!k){SERVER.expert=false;S.viewer='member';save();closeSheet();toast('로그아웃했어요.');syncNow();render();return}try{const d=await api('/api/health');if(!d.expert)throw new Error('키가 맞지 않아요.');S.viewer='expert';save();closeSheet();await syncNow();go('review');toast('전문가·관리자로 로그인했어요.')}catch(e){EXPERT_KEY='';try{localStorage.removeItem('jeju-cis-expert-key')}catch{}toast(e.status?e.message:e.message||'서버에 연결할 수 없어요.')}}
function review(){if(!SERVER.expert)return `${topbar('전문가 검토')}${empty('전문가·관리자 로그인이 필요해요','운영기관이 발급한 전문가 키로 로그인해 주세요.','expertLogin()','로그인')}`;const list=[...SERVER.list].sort((a,b)=>(a.public===0?0:1)-(b.public===0?0:1)||b.srv-a.srv),waiting=list.filter(x=>x.public===0).length;
 return `${topbar('전문가 검토',`<button class="text-btn" onclick="syncNow().then(render)">새로고침</button>`)}<div class="content" style="padding-bottom:0"><div class="eyebrow">EXPERT REVIEW · 서버</div><h2 style="font-size:19px;margin-top:6px">공개 검토 대기 ${waiting}건</h2><p class="body-copy">시민이 올린 기록은 여기서 공개를 승인하기 전까지 작성자와 전문가만 볼 수 있어요.</p></div>${list.map(x=>`<section class="expert-record review-record ${x.public===1?'is-public':x.public===-1?'is-hidden':''}"><div class="between"><img src="${photoUrl(x)}" alt="검토할 관찰 사진"><div><h3>${esc(x.name)}</h3>${badge(x.status)}<p class="hint">${esc(x.nickname)} · ${esc(x.region||'')} · ${fmt(x.at)}</p><p class="hint">정확한 위치 ${Number(x.lat).toFixed(5)}, ${Number(x.lon).toFixed(5)}</p><b class="pub-state">${x.public===1?'공개 중':x.public===-1?'비공개 처리':'공개 검토 대기'}</b></div></div>${x.note?`<p class="body-copy">${esc(x.note)}</p>`:''}<div class="review-pub"><button class="btn small ${x.public===1?'':'secondary'}" onclick="reviewApply(${x.srv},{public:1})">공개 승인</button><button class="btn small outline" onclick="reviewApply(${x.srv},{public:-1})">비공개</button><button class="btn small outline" onclick="reviewDelete(${x.srv})">삭제</button></div><label class="hint" for="rv-status-${x.srv}">동정 상태</label><select class="field-control" id="rv-status-${x.srv}">${[['requested','동정 요청됨'],['review','검토 중'],['done','동정 완료'],['unable','판별 불가'],['recorded','직접 기록']].map(([v,l])=>`<option value="${v}" ${x.status===v?'selected':''}>${l}</option>`).join('')}</select><label class="hint" for="rv-species-${x.srv}">동정 완료 시 생물종</label><select class="field-control" id="rv-species-${x.srv}"><option value="">(바꾸지 않음)</option>${SPECIES.map(s=>`<option ${x.name===s.name?'selected':''}>${s.name}</option>`).join('')}</select><label class="hint" for="rv-note-${x.srv}">전문가 의견</label><textarea class="field-control" rows="2" id="rv-note-${x.srv}" placeholder="예: 날개 무늬가 보이는 사진을 추가해 주세요.">${esc(x.expertNote||'')}</textarea><button class="btn full small" onclick="reviewSave(${x.srv})">동정 결과 저장</button></section>`).join('')||empty('검토할 기록이 없어요','시민이 기록을 올리면 여기에 나타나요.',"syncNow().then(render)",'새로고침')}`}
async function reviewApply(srv,patch){try{await api('/api/records/'+srv+'?device='+encodeURIComponent(DEVICE),{method:'PATCH',body:JSON.stringify(patch)});await syncNow();render();toast(patch.public===1?'공개했어요.':'비공개로 처리했어요.')}catch(e){toast(e.message||'서버에 연결할 수 없어요.')}}
async function reviewSave(srv){const status=$(`#rv-status-${srv}`).value,sp=SPECIES.find(s=>s.name===$(`#rv-species-${srv}`).value),expertNote=$(`#rv-note-${srv}`).value.trim();if(status==='unable'&&!expertNote){toast('판별이 어려운 이유나 필요한 사진을 의견으로 남겨 주세요.');return}if(status==='done'&&!sp&&SERVER.list.find(x=>x.srv===srv)?.name==='이름모름'){toast('동정 완료할 생물종을 골라 주세요.');return}
 const patch={status,expertNote:expertNote||(status==='done'?'사진의 특징을 확인하여 동정을 완료했습니다.':'')};if(sp)Object.assign(patch,{name:sp.name,scientific:sp.scientific,taxon:sp.taxon,nameLevel:'species'});await reviewApply(srv,patch)}
async function reviewDelete(srv){try{await api('/api/records/'+srv,{method:'DELETE'});await syncNow();render();toast('기록을 삭제했어요.')}catch(e){toast(e.message||'서버에 연결할 수 없어요.')}}
function expert(){""")
sub("const views={home,", "const views={review,home,")
sub("${menuItem('전문가 회원 신청','award','expertApplication()')}",
    "${menuItem('전문가 회원 신청','award','expertApplication()')}${LEGACY?'':menuItem(EXPERT_KEY?'전문가 검토 (서버)':'전문가·관리자 로그인','award',EXPERT_KEY?\"go('review')\":'expertLogin()')}")

# ---- 시트를 닫으면 미뤄 둔 화면 갱신 ----
sub("if(restore&&returnFocus?.isConnected)returnFocus.focus();returnFocus=null}", "if(restore&&returnFocus?.isConnected)returnFocus.focus();returnFocus=null;if(restore)setTimeout(refreshIfSafe)}")

# ---- 시작 시 동기화 ----
sub("if(!window.__CIS_HOST){window.addEventListener('hashchange',render);syncMode();render();}",
    "if(!window.__CIS_HOST){window.addEventListener('hashchange',render);syncMode();render();startSync();}")

sub('.cis-legacy-pin svg{', """.sync-line{display:flex;flex-direction:column;gap:2px;margin-top:12px;padding:10px 12px;border-radius:12px;font-size:12px;background:#f1f5f3;color:#5f6f68}.sync-line b{font-size:12px}
.sync-wait{background:#fff6e8;color:#9a5b00}.sync-err{background:#fdecec;color:#a33}.sync-rev{background:#eef4ff;color:#2f5aa8}.sync-pub{background:var(--mint);color:var(--deep)}.sync-hid{background:#f0f0f0;color:#666}
.review-record .pub-state{display:inline-block;margin-top:4px;font-size:11px;color:#2f5aa8}.review-record.is-public .pub-state{color:var(--green)}.review-record.is-hidden{opacity:.7}.review-record.is-hidden .pub-state{color:#888}
.review-pub{display:flex;gap:6px;margin:10px 0 4px}.review-pub .btn{flex:1;margin:0}
.cis-legacy-pin svg{""")

open(path, 'w', encoding='utf-8').write(s)
print('ok', path)
