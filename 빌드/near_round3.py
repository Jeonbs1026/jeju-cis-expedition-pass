# 피드백: 내 주변(8km) 지역을 생태지도에서 크게 표시. 사용: python3 near_round3.py <JEJU_CIS_최종.html>
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
assert 'function nearMe' not in s, '이미 적용됨'
def sub(a, b):
    global s
    assert s.count(a) == 1, (s.count(a), a[:70]); s = s.replace(a, b)
# 지도 모듈: 내 주변 지역은 원을 크게, 내 위치 점 표시, 내 위치 쪽으로 시작
sub("""      const rank=expeditionRank(area);
      const html=gap?expeditionMarker(area):`<button type="button" class="cis-cluster-marker cis-area-marker" data-area="${escape(area.name)}" style="--cis-cluster-size:42px" aria-label="${escape(area.name)} 관찰 ${area.count}건, 지역 정보"><strong>${area.count}</strong></button><span class="cis-cluster-name" style="top:47px">${escape(area.shortName)}</span>`;
      const marker=L.marker([area.lat,area.lon],{icon:L.divIcon({className:gap?'cis-gap-marker-wrap':'cis-cluster-wrap',html,iconSize:gap?[54,48]:[42,62],iconAnchor:gap?[27,48]:[21,21]})}).addTo(group);""",
"""      const rank=expeditionRank(area);
      // 내 주변(약 8km 안)의 지역은 원을 크게
      const near=!!options.near&&Math.hypot((area.lat-options.near.lat)*111,(area.lon-options.near.lon)*88.4)<=8,size=near?58:42;
      const html=gap?expeditionMarker(area):`<button type="button" class="cis-cluster-marker cis-area-marker${near?' is-near':''}" data-area="${escape(area.name)}" style="--cis-cluster-size:${size}px" aria-label="${escape(area.name)} 관찰 ${area.count}건${near?', 내 주변':''}, 지역 정보"><strong>${area.count}</strong></button><span class="cis-cluster-name${near?' is-near':''}" style="top:${size+5}px">${escape(area.shortName)}</span>`;
      const marker=L.marker([area.lat,area.lon],{zIndexOffset:near?500:0,icon:L.divIcon({className:gap?'cis-gap-marker-wrap':'cis-cluster-wrap',html,iconSize:gap?[54,48]:[size,size+20],iconAnchor:gap?[27,48]:[size/2,size/2]})}).addTo(group);""")
sub("""    if(gap){expeditionDecorations(host);arrangeExpeditionFlags(state,L,flags,group);}""",
    """    if(options.near)L.marker([options.near.lat,options.near.lon],{interactive:false,zIndexOffset:1000,icon:L.divIcon({className:'cis-me-wrap',html:'<span class="cis-me" aria-label="내 위치"></span>',iconSize:[18,18],iconAnchor:[9,9]})}).addTo(map);
    if(gap){expeditionDecorations(host);arrangeExpeditionFlags(state,L,flags,group);}""")
sub("else if(options.legacy)map.setView([33.4565,126.5615],15.5,{animate:false});else {const focus=",
    "else if(options.legacy)map.setView([33.4565,126.5615],15.5,{animate:false});else if(options.near)map.setView([options.near.lat,options.near.lon],10.5,{animate:false});else {const focus=")
# 앱: 지도에 '내 주변' 버튼, 권한이 있으면 자동
sub("mode:LEGACY?'eco':state.mode,legacy:LEGACY,", "mode:LEGACY?'eco':state.mode,legacy:LEGACY,near:LEGACY?null:state.near||null,")
sub('</div><div class="map-info">', """</div>${LEGACY?'':`<button class="near-btn ${state.near?'on':''}" onclick="nearMe()" aria-pressed="${!!state.near}">${icon('target')}내 주변</button>`}<div class="map-info">""")
sub("function mapHelp(){", r"""function nearMe(auto){if(state.near&&!auto){state.near=null;render();toast('내 주변 표시를 껐어요.');return}if(!navigator.geolocation){if(!auto)toast('위치를 사용할 수 없어요.');return}navigator.geolocation.getCurrentPosition(p=>{const lat=p.coords.latitude,lon=p.coords.longitude;if(!(lat>33.1&&lat<33.6&&lon>126.1&&lon<127)){if(!auto)toast('지금 위치가 제주 밖이에요.');return}state.near={lat,lon};if(route==='map')render();toast('내 주변 8km 안의 지역을 크게 보여 줘요.')},()=>{if(!auto)toast('위치를 불러오지 못했어요.')},{timeout:10000})}
function mapHelp(){""")
sub("if(route==='map'){if(LEGACY)opts.cityCounts=",
    "if(route==='map'&&!LEGACY&&!state.near&&!state.nearAsked){state.nearAsked=true;navigator.permissions?.query({name:'geolocation'}).then(p=>{if(p.state==='granted')nearMe(true)}).catch(()=>{})}\n if(route==='map'){if(LEGACY)opts.cityCounts=")
sub('.cis-legacy-pin svg{', """.near-btn{position:absolute;z-index:450;right:16px;top:62px;display:inline-flex;align-items:center;gap:5px;padding:8px 13px;border:0;border-radius:20px;background:#fff;box-shadow:0 2px 8px #233b1920;font:inherit;font-size:12px;font-weight:700;color:#5f6f68;cursor:pointer}.near-btn .icon{width:15px;height:15px}.near-btn.on{background:#2f7cf6;color:#fff}
.cis-cluster-marker.is-near{background:#2f7cf6e0;border-color:#2f7cf655;box-shadow:0 0 0 6px #2f7cf633}.cis-cluster-name.is-near{font-weight:800;color:#1d4fae}
.cis-me{display:block;width:18px;height:18px;border-radius:50%;background:#2f7cf6;border:3px solid #fff;box-shadow:0 0 0 0 #2f7cf688;animation:mePulse 1.8s infinite}@keyframes mePulse{70%{box-shadow:0 0 0 14px #2f7cf600}100%{box-shadow:0 0 0 0 #2f7cf600}}@media (prefers-reduced-motion:reduce){.cis-me{animation:none}}
.cis-legacy-pin svg{""")
open(p, 'w', encoding='utf-8').write(s); print('ok')
