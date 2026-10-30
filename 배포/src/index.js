// JEJU CIS 웹 시연물 서버 (Cloudflare Workers + D1)
// 원칙: 전문가·관리자가 공개 승인한 기록만 다른 사람에게 보임. 승인 전 기록·사진은 작성 기기와 전문가만.
//       정확한 좌표는 작성 기기와 전문가만, 다른 사람에게는 소수 둘째 자리(약 1km)로 낮춰 보냄.
const TAXA = ['plant', 'seaweed', 'insect', 'bird', 'mammal', 'herp'];
const DAILY_LIMIT = 30;          // 기기당 하루 등록 수
const PHOTO_MAX = 700_000;       // data URL 길이 (약 500KB JPEG)
const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type,X-Expert-Key',
};

const json = (data, status = 200) => new Response(JSON.stringify(data), { status, headers: { ...CORS, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } });
const fail = (status, message) => json({ error: message }, status);
const kstNow = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 16);
const str = (v, max) => typeof v === 'string' && v.length <= max ? v.trim() : null;
const SAFE = /^[^<>"'`\\]*$/;                           // 이름·닉네임·지역처럼 화면 코드 안에 들어가는 값
const safe = (v, max) => { const t = str(v, max); return t !== null && SAFE.test(t) ? t : null; };

function isExpert(req, env, url) {
  const key = req.headers.get('X-Expert-Key') || url.searchParams.get('k') || '';
  if (!env.EXPERT_KEY || key.length !== env.EXPERT_KEY.length) return false;
  let diff = 0;
  for (let i = 0; i < key.length; i++) diff |= key.charCodeAt(i) ^ env.EXPERT_KEY.charCodeAt(i);
  return diff === 0;
}

function toClient(row, device, expert) {
  const own = row.device === device;
  const exact = own || expert;
  return {
    srv: row.id, own, nickname: row.nickname, taxon: row.taxon, name: row.name, nameLevel: row.name_level,
    scientific: row.scientific, status: row.status, region: row.region, at: row.observed_at, createdAt: row.created_at,
    note: row.note, expertNote: row.expert_note, public: row.public, views: row.views, gap: !!row.gap, updatedAt: row.updated_at,
    bookmarks: row.bm ?? 0, bookmarked: !!row.mybm,
    lat: exact ? row.lat : Math.round(row.lat * 100) / 100, lon: exact ? row.lon : Math.round(row.lon * 100) / 100,
  };
}

// 작성·수정 요청의 기록 값 검사. 통과하면 저장할 값, 아니면 오류 문구
function readRecord(r) {
  if (!r || typeof r !== 'object') return '기록 값이 없어요.';
  const out = {
    taxon: TAXA.includes(r.taxon) ? r.taxon : null,
    name: safe(r.name, 40), name_level: ['species', 'group', 'unknown'].includes(r.nameLevel) ? r.nameLevel : 'species',
    scientific: safe(r.scientific || '', 80), status: ['requested', 'recorded'].includes(r.status) ? r.status : null,
    lat: Number(r.lat), lon: Number(r.lon), region: safe(r.region || '', 40), observed_at: str(r.at, 20),
    note: str(r.note || '', 500), photo: typeof r.photo === 'string' && r.photo.startsWith('data:image/jpeg;base64,') && r.photo.length <= PHOTO_MAX ? r.photo : null,
    gap: r.gap ? 1 : 0,
  };
  for (const [k, v] of Object.entries(out)) if (v === null || v === '' && ['name', 'observed_at'].includes(k)) return `잘못된 값: ${k}`;
  if (!(out.lat > 32.9 && out.lat < 33.8 && out.lon > 125.9 && out.lon < 127.2)) return '제주 안의 위치만 기록할 수 있어요.';
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(out.observed_at) || out.observed_at > kstNow()) return '관찰 일시가 올바르지 않아요.';
  return out;
}

// 제보 목록: 전문가는 전체, 일반은 내 기기 것만
async function reportList(db, device, expert) {
  const { results } = expert
    ? await db.prepare('SELECT * FROM reports ORDER BY id DESC LIMIT 300').all()
    : await db.prepare('SELECT * FROM reports WHERE device = ? ORDER BY id DESC').bind(device).all();
  return results.map(r => ({ srv: r.id, own: r.device === device, nickname: r.nickname, ref: r.ref, name: r.record_name, note: r.note, status: r.status, reply: r.reply, createdAt: r.created_at, updatedAt: r.updated_at }));
}

async function api(req, env, url) {
  const db = env.jeju_cis_db, path = url.pathname.replace(/\/+$/, ''), method = req.method;
  const device = url.searchParams.get('device') || '';
  const expert = isExpert(req, env, url);
  const idMatch = path.match(/^\/api\/records\/(\d+)(\/view|\/bookmark)?$/);
  const body = ['POST', 'PUT', 'PATCH'].includes(method) ? await req.json().catch(() => null) : null;
  const bodyDevice = body && typeof body.device === 'string' ? body.device : '';
  const validDevice = d => /^[A-Za-z0-9-]{8,64}$/.test(d);

  if (path === '/api/health') return json({ ok: true, expert });

  if (path === '/api/records' && method === 'GET') {
    // 변경 번호가 같으면 목록을 읽지 않고 '변경 없음'만 (번호에 전문가 여부 포함)
    const ver = `${(await db.prepare("SELECT v FROM meta WHERE k = 'version'").first())?.v ?? 0}:${expert ? 1 : 0}`;
    if (url.searchParams.get('v') === ver) return json({ unchanged: true, version: ver });
    const cols = `id,device,nickname,taxon,name,name_level,scientific,status,lat,lon,region,observed_at,created_at,note,expert_note,public,views,gap,updated_at,
      (SELECT COUNT(*) FROM bookmarks b WHERE b.record_id = records.id AND b.device <> ?1) AS bm,
      EXISTS (SELECT 1 FROM bookmarks b WHERE b.record_id = records.id AND b.device = ?1) AS mybm`;
    const sql = expert
      ? `SELECT ${cols} FROM records ORDER BY id DESC LIMIT 300`
      : `SELECT * FROM (SELECT ${cols} FROM records WHERE device = ?1) UNION ALL SELECT * FROM (SELECT ${cols} FROM records WHERE public = 1 AND device <> ?1 ORDER BY id DESC LIMIT 300) ORDER BY id DESC`;
    const { results } = await db.prepare(sql).bind(device).all();
    const reports = await reportList(db, device, expert);
    return json({ expert, now: kstNow(), version: ver, records: results.map(r => toClient(r, device, expert)), reports });
  }

  if (path === '/api/records' && method === 'POST') {
    if (!validDevice(bodyDevice)) return fail(400, '기기 정보가 없어요.');
    const nickname = safe(body.nickname || '', 20);
    if (!nickname) return fail(400, '닉네임을 확인해 주세요.');
    const rec = readRecord(body.record);
    if (typeof rec === 'string') return fail(400, rec);
    const since = new Date(Date.now() + 9 * 3600e3 - 864e5).toISOString().slice(0, 16);
    const { n } = await db.prepare('SELECT COUNT(*) AS n FROM records WHERE device = ? AND created_at > ?').bind(bodyDevice, since).first();
    if (n >= DAILY_LIMIT) return fail(429, '오늘 등록할 수 있는 기록 수를 넘었어요.');
    const now = kstNow();
    const row = await db.prepare(`INSERT INTO records (device,nickname,taxon,name,name_level,scientific,status,lat,lon,region,observed_at,created_at,note,photo,gap,updated_at)
      VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) RETURNING *`)
      .bind(bodyDevice, nickname, rec.taxon, rec.name, rec.name_level, rec.scientific, rec.status, rec.lat, rec.lon, rec.region, rec.observed_at, now, rec.note, rec.photo, rec.gap, now).first();
    return json({ record: toClient(row, bodyDevice, expert) }, 201);
  }

  if (path === '/api/reports' && method === 'GET') return json({ reports: await reportList(db, device, expert) });
  if (path === '/api/reports' && method === 'POST') {
    if (!validDevice(bodyDevice)) return fail(400, '기기 정보가 없어요.');
    const nickname = safe(body.nickname || '', 20), ref = str(body.ref || '', 30), name = safe(body.name || '', 40), note = str(body.note || '', 300);
    if (!nickname || !ref || !/^(srv|seed):\d+$/.test(ref) || !name || !note) return fail(400, '제보 내용을 확인해 주세요.');
    const since = new Date(Date.now() + 9 * 3600e3 - 864e5).toISOString().slice(0, 16);
    const { n } = await db.prepare('SELECT COUNT(*) AS n FROM reports WHERE device = ? AND created_at > ?').bind(bodyDevice, since).first();
    if (n >= 20) return fail(429, '오늘 보낼 수 있는 제보 수를 넘었어요.');
    const now = kstNow();
    const r = await db.prepare('INSERT INTO reports (device,nickname,ref,record_name,note,created_at,updated_at) VALUES (?,?,?,?,?,?,?) RETURNING id').bind(bodyDevice, nickname, ref, name, note, now, now).first();
    return json({ srv: r.id }, 201);
  }
  const reportMatch = path.match(/^\/api\/reports\/(\d+)$/);
  if (reportMatch && method === 'PATCH') {
    if (!expert) return fail(403, '전문가·관리자만 처리할 수 있어요.');
    const status = ['pending', 'accepted', 'rejected'].includes(body?.status) ? body.status : null, reply = str(body?.reply || '', 300);
    if (!status || reply === null) return fail(400, '처리 결과를 확인해 주세요.');
    const r = await db.prepare('UPDATE reports SET status=?, reply=?, updated_at=? WHERE id=? RETURNING id').bind(status, reply, kstNow(), Number(reportMatch[1])).first();
    return r ? json({ ok: true }) : fail(404, '제보를 찾을 수 없어요.');
  }

  if (!idMatch) return fail(404, '없는 주소예요.');
  const id = Number(idMatch[1]);
  const row = await db.prepare('SELECT * FROM records WHERE id = ?').bind(id).first();
  if (!row) return fail(404, '기록을 찾을 수 없어요.');

  if (idMatch[2] === '/bookmark') { // 북마크: 기기당 1회, 공개 기록 또는 내 기록
    if (method !== 'POST' || !validDevice(bodyDevice)) return fail(400, '기기 정보가 없어요.');
    if (row.public !== 1 && row.device !== bodyDevice) return fail(403, '공개된 기록만 북마크할 수 있어요.');
    if (body.on) await db.prepare('INSERT OR IGNORE INTO bookmarks (device, record_id, created_at) VALUES (?,?,?)').bind(bodyDevice, id, kstNow()).run();
    else await db.prepare('DELETE FROM bookmarks WHERE device = ? AND record_id = ?').bind(bodyDevice, id).run();
    return json({ ok: true });
  }
  if (idMatch[2]) { // 조회수: 공개 기록만, 남의 기록만
    if (method !== 'POST') return fail(405, '허용되지 않는 요청이에요.');
    if (row.public === 1 && row.device !== bodyDevice) await db.prepare('UPDATE records SET views = views + 1 WHERE id = ?').bind(id).run();
    return json({ ok: true });
  }

  if (method === 'PUT') { // 작성 기기의 수정: 동정 완료 전만, 수정하면 다시 검수
    if (row.device !== bodyDevice || !validDevice(bodyDevice)) return fail(403, '내 기록만 수정할 수 있어요.');
    if (row.status === 'done') return fail(409, '동정 완료 후에는 수정할 수 없어요.');
    const rec = readRecord(body.record);
    if (typeof rec === 'string') return fail(400, rec);
    const updated = await db.prepare(`UPDATE records SET taxon=?,name=?,name_level=?,scientific=?,status=?,lat=?,lon=?,region=?,observed_at=?,note=?,photo=?,gap=?,public=0,expert_note='',updated_at=? WHERE id=? RETURNING *`)
      .bind(rec.taxon, rec.name, rec.name_level, rec.scientific, rec.status, rec.lat, rec.lon, rec.region, rec.observed_at, rec.note, rec.photo, rec.gap, kstNow(), id).first();
    return json({ record: toClient(updated, bodyDevice, expert) });
  }

  if (method === 'PATCH') { // 전문가·관리자: 동정 결과, 의견, 공개 여부
    if (!expert) return fail(403, '전문가·관리자만 처리할 수 있어요.');
    const status = ['requested', 'review', 'done', 'unable', 'recorded'].includes(body?.status) ? body.status : row.status;
    const pub = [-1, 0, 1].includes(body?.public) ? body.public : row.public;
    const name = safe(body?.name ?? row.name, 40) || row.name, scientific = safe(body?.scientific ?? row.scientific, 80) ?? row.scientific;
    const taxon = TAXA.includes(body?.taxon) ? body.taxon : row.taxon, level = ['species', 'group', 'unknown'].includes(body?.nameLevel) ? body.nameLevel : row.name_level;
    const note = str(body?.expertNote ?? row.expert_note, 500) ?? row.expert_note;
    if (status === 'unable' && !note) return fail(400, '판별 불가에는 전문가 의견이 필요해요.');
    const updated = await db.prepare('UPDATE records SET status=?,public=?,name=?,scientific=?,taxon=?,name_level=?,expert_note=?,updated_at=? WHERE id=? RETURNING id,device,nickname,taxon,name,name_level,scientific,status,lat,lon,region,observed_at,created_at,note,expert_note,public,views,gap,updated_at')
      .bind(status, pub, name, scientific, taxon, level, note, kstNow(), id).first();
    return json({ record: toClient(updated, device, true) });
  }

  if (method === 'DELETE') { // 작성 기기(동정 완료 전) 또는 전문가·관리자
    const own = row.device === device && validDevice(device);
    if (!expert && !(own && row.status !== 'done')) return fail(403, '삭제할 수 없는 기록이에요.');
    await db.batch([db.prepare('DELETE FROM records WHERE id = ?').bind(id), db.prepare('DELETE FROM bookmarks WHERE record_id = ?').bind(id)]);
    return json({ ok: true });
  }
  return fail(405, '허용되지 않는 요청이에요.');
}

async function photo(req, env, url, id) {
  const row = await env.jeju_cis_db.prepare('SELECT device, public, photo FROM records WHERE id = ?').bind(id).first();
  const device = url.searchParams.get('device') || '';
  if (!row || !(row.public === 1 || row.device === device || isExpert(req, env, url))) return new Response('not found', { status: 404, headers: CORS });
  const [head, data] = row.photo.split(',');
  const bytes = Uint8Array.from(atob(data), c => c.charCodeAt(0));
  return new Response(bytes, { headers: { ...CORS, 'Content-Type': head.slice(5, head.indexOf(';')), 'Cache-Control': row.public === 1 ? 'public, max-age=300' : 'private, no-store' } });
}

// 앱 HTML: 처음 요청 때 내용 해시로 ETag를 만들어 기억(배포하면 새 인스턴스에서 다시 계산)
let page = null;
async function servePage(req, env, url) {
  if (!page) {
    const r = await env.ASSETS.fetch(new Request(new URL('/', url), { headers: { 'Accept-Encoding': 'identity' } }));
    const body = await r.arrayBuffer(), hash = new Uint8Array(await crypto.subtle.digest('SHA-256', body));
    // 약한 ETag: Cloudflare가 압축하면서 강한 ETag는 지우기 때문
    page = { body, etag: 'W/"' + [...hash.slice(0, 10)].map(b => b.toString(16).padStart(2, '0')).join('') + '"',
      // 수정 시각도 내용 해시로 정함 → 어느 인스턴스에서든 같은 내용이면 같은 값 (2020년부터 약 5년 범위의 과거 시각)
      modified: new Date(Date.UTC(2020, 0, 1) + (((hash[0] << 24) | (hash[1] << 16) | (hash[2] << 8) | hash[3]) >>> 0) % (5 * 365 * 86400) * 1000) };
  }
  const headers = { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=0, must-revalidate', ETag: page.etag, 'Last-Modified': page.modified.toUTCString() };
  const plain = t => t.trim().replace(/^W\//, '');
  if ((req.headers.get('If-None-Match') || '').split(',').some(t => plain(t) === plain(page.etag))) return new Response(null, { status: 304, headers });
  // Cloudflare가 압축하면서 ETag를 지우므로 수정 시각으로 확인. 내용이 바뀌면 값이 달라지도록 '같을 때만' 304
  const since = Date.parse(req.headers.get('If-Modified-Since') || '');
  if (!req.headers.get('If-None-Match') && since === page.modified.getTime()) return new Response(null, { status: 304, headers });
  return new Response(page.body, { headers });
}

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (req.method === 'OPTIONS') return new Response(null, { headers: CORS });
    const photoMatch = url.pathname.match(/^\/api\/photo\/(\d+)$/);
    try {
      if (photoMatch && req.method === 'GET') return await photo(req, env, url, Number(photoMatch[1]));
      if (url.pathname.startsWith('/api/')) {
        const res = await api(req, env, url);
        // 쓰기가 성공하면 변경 번호 증가 (조회수는 자주 바뀌어 제외)
        if (res.ok && req.method !== 'GET' && !url.pathname.endsWith('/view')) await env.jeju_cis_db.prepare("UPDATE meta SET v = v + 1 WHERE k = 'version'").run();
        return res;
      }
    } catch (e) {
      return fail(500, '서버에서 처리하지 못했어요.');
    }
    if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) return servePage(req, env, url);
    return env.ASSETS.fetch(req);
  },
};
