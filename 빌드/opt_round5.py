# 디버깅: 서버 글자 거르기(XSS 방어 2중), 서버에서 삭제된 내 기록 표시, 삭제된 기록 수정 시 새로 등록
# 사용: python3 opt_round5.py <JEJU_CIS_최종.html>
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
assert "sync==='gone'" not in s, '이미 적용됨'
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:70]); s = s.replace(a, b)
sub("function fromServer(x){return {id:SRV_ID+x.srv,srv:x.srv,remote:true,author:x.nickname===ME?x.nickname+'·':x.nickname,photo:photoUrl(x),taxon:x.taxon,name:x.name,nameLevel:x.nameLevel,scientific:x.scientific,status:x.status,lat:x.lat,lon:x.lon,region:x.region,",
    "// 서버 값이 화면 코드(onclick 등)에 들어가도 안전하도록 따옴표·꺾쇠·역슬래시 제거 (서버 검사와 2중)\n"
    "const clean=v=>String(v??'').replace(/[<>\"'`\\\\]/g,'');\n"
    "function fromServer(x){const nick=clean(x.nickname);return {id:SRV_ID+x.srv,srv:x.srv,remote:true,author:nick===ME?nick+'·':nick,photo:photoUrl(x),taxon:x.taxon,name:clean(x.name),nameLevel:x.nameLevel,scientific:clean(x.scientific),status:x.status,lat:x.lat,lon:x.lon,region:clean(x.region),")
sub(" S.records.forEach(r=>{const x=r.author===ME&&r.srv&&r.sync==='done'&&own.get(r.srv);if(!x)return;",
    " S.records.forEach(r=>{if(r.author===ME&&r.srv&&r.sync==='done'&&!own.has(r.srv)){r.sync='gone';changed=true;return}const x=r.author===ME&&r.srv&&r.sync==='done'&&own.get(r.srv);if(!x)return;")
sub(a404 := " try{const d=r.srv?await api('/api/records/'+r.srv,{method:'PUT',body:JSON.stringify(body)}):await api('/api/records',{method:'POST',body:JSON.stringify(body)});",
    " try{const post=()=>api('/api/records',{method:'POST',body:JSON.stringify(body)});let d;if(r.srv){try{d=await api('/api/records/'+r.srv,{method:'PUT',body:JSON.stringify(body)})}catch(e){if(e.status!==404)throw e;d=await post()}}else d=await post(); /* 서버에서 지워진 기록을 고치면 바로 새로 등록 */")
sub("const t=r.sync==='pending'?['wait','서버 전송 대기','연결되면 자동으로 올라가요.']:",
    "const t=r.sync==='gone'?['hid','서버에서 삭제됨','전문가·관리자가 삭제한 기록이에요. 이 기기에만 남아 있어요.']:r.sync==='pending'?['wait','서버 전송 대기','연결되면 자동으로 올라가요.']:")
open(p, 'w', encoding='utf-8').write(s); print('ok')
