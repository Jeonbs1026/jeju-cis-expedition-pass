# JEJU 익스페디션 패스 (JEJU CIS 앱 고도화)

2026 JEJU CIS 시민과학 앱 고도화 공모전 · 팀 그린패스 (정기우, 김범준)

JEJU CIS 앱을 '기록하고 끝나는 앱'에서 '성장하는 탐험 앱'으로 고도화한 **웹 시연물**입니다. 기존 앱의 화면 구성을 유지했고, 화면 맨 위의 `기존 앱 | 개선 앱` 버튼으로 같은 화면에서 바뀐 점을 비교할 수 있습니다.

- **시연 주소:** https://jeju-cis.jeju-cis.workers.dev (설치 없이 휴대폰·PC 브라우저로 실행)
- **결과 보고서(3쪽 설명서):** `JEJU_CIS_최종보고서.docx`

## 파일 구성
| 경로 | 내용 |
|---|---|
| `JEJU_CIS_최종.html` | 웹 시연물 전체 (HTML 파일 하나. 브라우저로 열면 동작) |
| `JEJU_CIS_최종발표.html` | 발표 덱 13장 (최종 앱 내장, 로컬에서 열어 사용) |
| `발표대본.md` | 장별 발표 대본과 예상 질문 |
| `발표당일_체크리스트.md` | 실기기 확인, 리허설, 당일 준비, 문제 대응 |
| `JEJU_CIS_최종보고서.docx` | 최종 발표 보고서 겸 3쪽 설명서 |
| `배포/` | 시연용 서버 (Cloudflare Workers + D1): `src/index.js`, `schema.sql`, `wrangler.jsonc` |
| `빌드/` | 앱·덱 수정 스크립트와 자동 검사 스크립트 |

## 구현 기능 요약
- **과제 1 · 기능 고도화**
  - 등록: 분류 선택 취소, 날짜·시간 한 화면 입력, 중앙 핀 고정, 수정 제한 안내, 현재 위치 읍·면·동 자동 입력
  - 동정: 요청 접수 → 검토 중 → 완료·판별 불가 단계, 전문가 의견, 결과 알림, 오동정 제보 처리
  - 지도: 제주 전체 읍·면·동 집계, 탐험도, 위치 공개 2단계, 내 주변 강조
  - 탐색: 정렬(최신·오래된·북마크·조회순), 조회수, 필터, 같은 종 모아보기
- **과제 2 · 사용자 활성화:** 포인트(출석·받은 북마크 포함), 등급 로드맵, 배지 12종, 주간 미션과 홈 위젯, 주간·월간 랭킹
- **과제 3 · 신규 기능:** 탐험 리포트, 전문가 검수 후 공개되는 기록 공유, 전문가 검토 화면, 오프라인 임시저장과 자동 동기화

## 실행 방법
- **그냥 써 보기:** 시연 주소에 접속하거나 `JEJU_CIS_최종.html`을 브라우저로 열기. 서버 기능은 인터넷 연결 시 동작합니다.
- **전문가 기능:** 설정 → 전문가·관리자 로그인 → 전문가 키 입력. 키는 저장소에 포함하지 않으며 별도로 전달합니다.

### 서버 배포 (Cloudflare 계정 필요)
```
cd 배포
cp ../JEJU_CIS_최종.html public/index.html                      # 배포할 앱 (저장소에는 포함하지 않음)
npx wrangler d1 execute jeju-cis-db --remote --file schema.sql  # 처음 한 번 (테이블 생성)
npx wrangler secret put EXPERT_KEY                               # 전문가 키 설정
npx wrangler deploy
```

### 자동 검사 (Node.js와 Chrome 필요)
| 스크립트 | 내용 |
|---|---|
| `node 빌드/api_test.mjs <주소> <전문가키>` | 서버 권한·공개 규칙 16개 |
| `node 빌드/api_test2.mjs <주소> <전문가키>` | 북마크·제보 API 12개 |
| `node 빌드/e2e_server.mjs <전문가키>` | 기기 2대: 등록 → 승인 → 알림 → 공개 → 오프라인 동기화 |
| `node 빌드/e2e_round2.mjs <전문가키>` | 제보·현재 위치·미션·출석·배지·북마크 포인트 |
| `node 빌드/e2e_round3.mjs` | 내 주변 표시, 안내 문구 |
| `node 빌드/e2e_round5.mjs <전문가키>` | 서버에서 삭제된 기록 처리, 입력 거르기(XSS) |
| `node 빌드/app_regress.mjs <주소> [전문가키]` | 기존·개선 모드 60개 화면 |
| `node 빌드/deck_check.mjs <덱 절대경로>` | 발표 덱 13장과 내장 앱 |
| `node 빌드/perf_slow.mjs [주소]` | 저사양 조건 로딩 시간 |

검사는 실제 서버에 테스트 기록을 만들고 끝에서 지웁니다. `e2e_round5.mjs`는 D1에 직접 SQL을 실행하므로 `배포/` 폴더에서 wrangler 로그인이 되어 있어야 합니다.

## 구성에 대해
개발계획서에서는 Next.js·TypeScript PWA와 Firebase·Vercel을 계획했습니다. 보안상 연구소와 원본 소스 등 파일을 교환할 수 없어 결과물이 '보고 재구현하는 시연물'이 되었고, 기존 앱의 기술 구조도 공유받을 수 없어 구성을 바꾸었습니다.
- 빌드 없이 바로 열리는 HTML 단일 파일
- 설치 없는 웹
- 시연용 서버 (Cloudflare Workers + D1)

이 구성은 시연을 위한 것이며, 운영 앱에 같은 구성을 제안하는 것은 아닙니다. 운영 앱 반영은 상태 흐름·데이터 항목·처리 규칙 단위로 정리했습니다(보고서 참고).

## 외부 코드·데이터·도구 출처
| 구분 | 이름 | 라이선스·출처 | 쓰인 곳 |
|---|---|---|---|
| 지도 | Leaflet 1.9.4 | BSD-2-Clause | 앱 |
| 지도 | MapLibre GL JS, leaflet-maplibre-gl | BSD-3-Clause · © MapLibre contributors, Mapbox | 앱 |
| 지도 데이터 | OpenFreeMap 배경지도 | © OpenMapTiles, © OpenStreetMap contributors | 앱 (실행 시 불러옴) |
| 사진 정보 | exifr | MIT | 앱 |
| QR | qrcode-generator 2.0.4 (Kazuhiko Arase) | MIT | 발표 덱 |
| 글꼴 | Pretendard | SIL Open Font License 1.1 | 발표 덱 |
| 생물 설명 | 국립생물자원관, 국립중앙과학관 자료 | 앱 화면에 출처 링크 표시, 요약해 사용 | 앱 |
| 서버 | Cloudflare Workers, D1 | Cloudflare 무료 플랜 | 시연 서버 |
| AI 도구 | Claude Code (Anthropic) | — | 코드 작성·수정, 자동 검사, 문서 초안 작성 |

예시 생물 사진의 출처는 팀이 확인한 뒤 이 표에 추가합니다.
