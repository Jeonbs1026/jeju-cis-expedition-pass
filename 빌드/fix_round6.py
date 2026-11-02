# 라운드6(11/2): 같은 화면 다시 그릴 때 스크롤 유지, 전문가 의견 표시·알림, 검토 저장 문구, 삭제 확인. 사용: python3 fix_round6.py <앱.html>
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:60]); s = s.replace(a, b)
# 1. 화면(주소)이 바뀔 때만 맨 위로
sub("renderNav();window.scrollTo(0,0);", "renderNav();if(window.__view!==location.hash){window.scrollTo(0,0);window.__view=location.hash}")
# 2. 서버 기록의 전문가 의견은 '예시'가 아님 + 동정 완료 알림에 의견 포함
sub("<strong>전문가 의견 · 예시</strong>", "<strong>전문가 의견${r.srv?'':' · 예시'}</strong>")
sub("notifyStatus(r,t,x.status==='done'?`${x.name}로 동정이 완료되었어요.`:x.expertNote||'')",
    "notifyStatus(r,t,x.status==='done'?`${x.name}로 동정이 완료되었어요.${x.expertNote?' 전문가 의견: '+x.expertNote:''}`:x.expertNote||'')")
# 3. 저장 문구, 삭제 확인
sub("async function reviewApply(srv,patch){", "async function reviewApply(srv,patch,msg){")
sub("toast(patch.public===1?'공개했어요.':'비공개로 처리했어요.')", "toast(msg||(patch.public===1?'공개했어요.':'비공개로 처리했어요.'))")
sub("await reviewApply(srv,patch)}", "await reviewApply(srv,patch,'동정 결과를 저장했어요.')}")
sub("async function reviewDelete(srv){try{", """async function reviewDelete(srv,ok){if(!ok){const x=SERVER.list.find(x=>x.srv===srv);sheet('이 기록을 삭제할까요?',`<p>${esc(x?.name||'기록')} · ${esc(x?.nickname||'')}</p><p>삭제하면 되돌릴 수 없어요. 다른 사람에게 보이지 않게만 하려면 '비공개'를 눌러 주세요.</p><button class="btn full" style="background:#c62828" onclick="reviewDelete(${srv},1)">삭제하기</button><button class="btn outline full" onclick="closeSheet()">취소</button>`);return}closeSheet();try{""")
open(p, 'w', encoding='utf-8').write(s); print('ok')
