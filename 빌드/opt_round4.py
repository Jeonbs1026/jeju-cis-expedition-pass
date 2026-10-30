# 최적화: 변경 번호로 바뀐 게 없으면 목록을 다시 받지 않음, 기록·제보를 한 번에 받기, 알림 개수 제한
# 사용: python3 opt_round4.py <JEJU_CIS_최종.html>
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
assert 'function applyReports' not in s, '이미 적용됨'
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:70]); s = s.replace(a, b)
sub("async function pullReports(){const d=await api('/api/reports?device='+encodeURIComponent(DEVICE));SERVER.reports=d.reports;const by=new Map(d.reports.filter(",
    "function applyReports(list){SERVER.reports=list;const by=new Map(list.filter(")
sub("await pushPending();await pushReports();await pullReports();await pull()", "await pushPending();await pushReports();await pull()")
sub("async function pull(){const d=await api('/api/records?device='+encodeURIComponent(DEVICE));SERVER.ok=true;SERVER.expert=!!d.expert;SERVER.list=d.records;",
    "async function pull(){const d=await api('/api/records?device='+encodeURIComponent(DEVICE)+(SERVER.ver?'&v='+encodeURIComponent(SERVER.ver):''));SERVER.ok=true;\n"
    " // 서버 데이터가 그대로면 목록을 다시 처리하지 않음 (서버도 1행만 읽음)\n"
    " if(d.unchanged){if(SERVER.pushed){SERVER.pushed=false;SERVER.dirty=true;refreshIfSafe()}return}\n"
    " SERVER.ver=d.version;SERVER.expert=!!d.expert;SERVER.list=d.records;applyReports(d.reports||[]);")
sub("async function saveExpertKey(out){const k=out?'':$('#expert-key').value.trim();EXPERT_KEY=k;",
    "async function saveExpertKey(out){const k=out?'':$('#expert-key').value.trim();EXPERT_KEY=k;SERVER.ver='';")
# 알림은 최근 60개까지만 기기에 보관 (저장 공간)
sub("function notifyStatus(r,title,body){S.notifications.unshift({id:Date.now()+Math.random(),record:r.id,title,body,at:fmt(localNow()),read:false});",
    "function notifyStatus(r,title,body){S.notifications.unshift({id:Date.now()+Math.random(),record:r.id,title,body,at:fmt(localNow()),read:false});S.notifications=S.notifications.slice(0,60);")
open(p, 'w', encoding='utf-8').write(s); print('ok')
