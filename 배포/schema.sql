-- JEJU CIS 웹 시연물 서버 저장소 (Cloudflare D1)
-- 공개(public=1)는 전문가·관리자가 승인한 기록만. 승인 전에는 작성 기기와 전문가만 볼 수 있음
CREATE TABLE IF NOT EXISTS records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device TEXT NOT NULL,            -- 작성 기기 식별자(무작위). 계정 대신 사용
  nickname TEXT NOT NULL,
  taxon TEXT NOT NULL,
  name TEXT NOT NULL,
  name_level TEXT NOT NULL DEFAULT 'species',
  scientific TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL,            -- requested | review | done | unable | recorded
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  region TEXT NOT NULL DEFAULT '',
  observed_at TEXT NOT NULL,
  created_at TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT '',
  photo TEXT NOT NULL,             -- 압축한 JPEG data URL
  expert_note TEXT NOT NULL DEFAULT '',
  public INTEGER NOT NULL DEFAULT 0, -- 0 검수 대기, 1 공개, -1 비공개 처리
  views INTEGER NOT NULL DEFAULT 0,
  gap INTEGER NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS records_device ON records(device);
CREATE INDEX IF NOT EXISTS records_public ON records(public);

-- 북마크(좋아요): 기기별 1회. 받은 북마크는 작성자 포인트로
CREATE TABLE IF NOT EXISTS bookmarks (
  device TEXT NOT NULL,
  record_id INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (device, record_id)
);
-- 오동정 제보: 시민 제보 → 전문가가 반영됨/반영 안 함으로 처리
CREATE TABLE IF NOT EXISTS reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device TEXT NOT NULL,
  nickname TEXT NOT NULL,
  ref TEXT NOT NULL,               -- srv:<서버 기록 id> 또는 seed:<예시 기록 id>
  record_name TEXT NOT NULL,
  note TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending', -- pending | accepted | rejected
  reply TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS reports_device ON reports(device);
-- 기록별 북마크 수 집계용 (목록 조회 때 북마크 전체를 훑지 않도록)
CREATE INDEX IF NOT EXISTS bookmarks_record ON bookmarks(record_id, device);
-- 데이터 변경 번호: 쓰기가 성공할 때마다 1 증가. 조회 때 번호가 같으면 목록을 다시 읽지 않음
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v INTEGER NOT NULL);
INSERT OR IGNORE INTO meta (k, v) VALUES ('version', 0);
