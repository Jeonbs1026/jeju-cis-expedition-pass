// 최종 발표 보고서 겸 3쪽 설명서(docx). 서식은 중간발표 보완자료(hwpx)를 따름:
// 가운데 제목 상자 · ◇ 회색 소제목 표 · 검정 번호 칸 장 제목 · 검정 테두리 표 · ※ 주석 · "- n -" 쪽번호 · 맑은 고딕
// 사용: NODE_PATH=<docx 설치 폴더>/node_modules node report_docx.js <출력.docx>
const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  BorderStyle, ShadingType, VerticalAlign, Footer, PageNumber, TableLayoutType,
} = require('docx');

const OUT = process.argv[2] || 'JEJU_CIS_최종보고서.docx';
const FONT = { ascii: 'Malgun Gothic', hAnsi: 'Malgun Gothic', eastAsia: '맑은 고딕', cs: 'Malgun Gothic' };
const MARGIN = 850, REAL_W = 11906 - MARGIN * 2, W = 9866, K = REAL_W / W; // 너비는 9866 기준으로 적고 실제 폭(여백 15mm)에 맞춰 비례
const dx = w => Math.round(w * K);
const GRAY = 'D9D9D9', LINE = { style: BorderStyle.SINGLE, size: 6, color: '000000' };
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const ALL = { top: LINE, bottom: LINE, left: LINE, right: LINE };
const SZ = 18;                           // 본문 9pt (3쪽 안에 맞춤)

// "**굵게**" 표시를 TextRun으로
function runs(text, opt = {}) {
  return String(text).split(/(\*\*[^*]+\*\*)/).filter(Boolean).map(t => t.startsWith('**')
    ? new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, size: opt.size || SZ, color: opt.color })
    : new TextRun({ text: t, bold: !!opt.bold, font: FONT, size: opt.size || SZ, color: opt.color }));
}
const para = (text, opt = {}) => new Paragraph({
  alignment: opt.align || AlignmentType.LEFT, keepNext: !!opt.keepNext, spacing: { before: opt.before ?? 0, after: opt.after ?? 50, line: opt.line || 264 },
  indent: opt.indent, children: runs(text, opt),
});
const note = text => para('※ ' + text, { size: 16, after: 30, indent: { left: 200, hanging: 200 } });

function cell(content, w, opt = {}) {
  const lines = Array.isArray(content) ? content : [content];
  return new TableCell({
    width: { size: dx(w), type: WidthType.DXA }, columnSpan: opt.span, verticalAlign: opt.valign || VerticalAlign.CENTER,
    shading: opt.fill ? { type: ShadingType.CLEAR, color: 'auto', fill: opt.fill } : undefined,
    borders: opt.borders || ALL, margins: { top: 35, bottom: 35, left: 90, right: 90 },
    children: lines.map(l => para(l, { bold: opt.bold, align: opt.align, size: opt.size, color: opt.color, after: 0, line: 252, keepNext: opt.keepNext })),
  });
}
const table = (widths, rows) => new Table({ width: { size: REAL_W, type: WidthType.DXA }, columnWidths: widths.map(dx), layout: TableLayoutType.FIXED, rows });
const gap = (after = 120) => new Paragraph({ spacing: { after, before: 0 }, children: [] });

// 문서 제목 상자 (가운데)
const titleBox = text => table([W], [new TableRow({ children: [cell(text, W, { bold: true, size: 32, align: AlignmentType.CENTER })] })]);

// 장 제목: 검정 번호 칸 + 제목, 아래 굵은 선
function chapter(n, text, newPage = false) {
  const thick = { style: BorderStyle.SINGLE, size: 18, color: '000000' };
  // 새 쪽에서 시작하면 제목이 쪽 끝에 홀로 남지 않음
  return [newPage ? new Paragraph({ pageBreakBefore: true, spacing: { after: 0 }, children: [] }) : gap(80), table([620, W - 620], [new TableRow({ children: [
    cell(`${n}.`, 620, { keepNext: true, fill: '000000', color: 'FFFFFF', bold: true, size: 23, align: AlignmentType.CENTER, borders: { top: NONE, left: NONE, right: NONE, bottom: thick } }),
    cell(text, W - 620, { keepNext: true, bold: true, size: 24, borders: { top: NONE, left: NONE, right: NONE, bottom: thick } }),
  ] })]), gap(80)];
}

// ◇ 소제목 + 표 (첫 줄은 회색 소제목, 둘째 줄은 회색 머리행)
function block(title, widths, head, rows, opt = {}) {
  const out = [];
  if (title) out.push(new TableRow({ cantSplit: true, children: [cell('◇ ' + title, W, { span: widths.length, fill: GRAY, bold: true, size: 19, keepNext: true })] }));
  if (head) out.push(new TableRow({ tableHeader: true, cantSplit: true, children: head.map((h, i) => cell(h, widths[i], { fill: GRAY, bold: true, align: AlignmentType.CENTER, keepNext: true })) }));
  rows.forEach(r => out.push(new TableRow({ children: r.map((c, i) => cell(c, widths[i], {
    align: opt.center?.includes(i) ? AlignmentType.CENTER : AlignmentType.LEFT, bold: opt.boldCols?.includes(i), fill: opt.fillCols?.includes(i) ? 'F2F2F2' : undefined,
  })) })));
  return table(widths, out);
}

const URL_ = 'https://jeju-cis.jeju-cis.workers.dev';
const body = [
  titleBox('JEJU CIS 앱 고도화 결과 보고서'),
  gap(140),
  block('문서 개요', [1500, 3433, 1500, 3433], null, [
    ['팀명', '그린패스 (정기우·김범준)', '제안명', 'JEJU 익스페디션 패스'],
    ['결과물', '웹 시연물 (설치 없이 브라우저로 실행)', '구분', '최종 발표 보고서 · 3쪽 설명서'],
    ['시연 주소', URL_, '작성일', '2026년 10월 31일'],
  ], { fillCols: [0, 2], boldCols: [0, 2], center: [0, 2] }),
  gap(100),
  para('기존 앱을 쓰면서 확인한 불편을 줄이고, 시민이 기록을 계속 남기도록 돕는 기능을 웹 시연물로 구현했습니다. 기존 앱의 화면 구성을 유지했으며, 화면 맨 위 **‘기존 앱 | 개선 앱’** 버튼으로 같은 화면에서 바뀐 점을 바로 비교할 수 있습니다.'),

  ...chapter(1, '구현 범위'),
  block(null, [1550, 6216, 2100], ['과제', '구현한 기능', '확인 위치'], [
    ['과제 1\n기능 고도화', [
      '**등록** 분류 선택 취소, 날짜·시간 한 화면 입력, 지도 중앙 핀 고정, 상단 고정, 동정 요청 전 수정 제한 안내, 현재 위치를 읍·면·동으로 자동 입력',
      '**동정** 요청 접수 → 검토 중 → 동정 완료·판별 불가 단계 표시, 전문가 의견, 결과 알림, 오동정 제보 처리 현황',
      '**지도** 제주 전체의 읍·면·동별 기록 수, 기록이 적은 곳을 찾는 탐험도, 위치 공개 2단계, 내 주변 지역 강조',
      '**탐색** 최신·오래된·북마크·조회순 정렬, 조회수, 홈 필터, 같은 종 모아보기'], '등록(가운데 버튼), 활동내역, 관찰 상세, 생태지도, 홈·아카이브'],
    ['과제 2\n사용자 활성화', [
      '**포인트** 기록·완성·탐사 필요 지역·동정 완료·제주 첫 기록·주간 미션·출석(연속 보너스)·받은 북마크',
      '**성장** 등급 로드맵과 다음 등급까지의 진행률, 배지 12종(분류·지역·정확도 포함), 포인트 이력',
      '**참여** 주간 탐사 미션과 홈 미션 위젯, 주간·월간 랭킹(포인트·기록·조회수 기준, 활동 0건 제외)'], '마이 → 나의 성장, 전체 메뉴 → 랭킹, 홈'],
    ['과제 3\n신규 기능', [
      '**탐험 리포트** 기록·종·지역 수, 연구 활용 가능 기록 비율, 주별·분류별 통계, 다음 탐사 지역 추천',
      '**검수 후 공개되는 기록 공유** 시민이 올린 기록은 전문가가 공개를 승인한 뒤에만 다른 사람에게 보임, 전문가 검토 화면',
      '**오프라인 임시저장** 연결이 없으면 기기에 저장하고 연결되면 자동 전송',
      '**읽을거리** 전문가 칼럼과 관찰 기록 등록 가이드(예시 콘텐츠)'], '마이 → 탐험 리포트, 설정 → 전문가·관리자 로그인'],
  ].map(r => [r[0].split('\n'), r[1], r[2]]), { center: [0], boldCols: [0], fillCols: [0] }),
  gap(60),
  note('기존 앱 모드는 실제 앱 화면 캡처와 사용성 점검 자료를 근거로 재현했습니다. 날짜·시간 팝업(02)은 재현하지 않았습니다.'),
  note('서버 푸시는 아이폰에서 앱 설치가 필요해 앱을 열어 둔 동안 받는 알림으로 대체했고, 실제 JEJU CIS 회원 연동은 할 수 없어 기기별 닉네임과 전문가 키를 사용합니다.'),

  ...chapter(2, '사용 기술 (시연물의 실제 구성)', true),
  block(null, [1550, 4100, 4216], ['구분', '구성', '역할'], [
    ['화면', 'HTML·CSS·JavaScript 단일 파일 (별도 프레임워크 없음)', '앱 전체 화면, 기존/개선 모드 전환, 넓은 화면에서 휴대폰 비율 표시'],
    ['지도', 'Leaflet 1.9.4, MapLibre GL, OpenFreeMap 배경지도, 내장 해안선', '생태지도·탐험도·위치 선택, 배경지도를 못 불러와도 해안선으로 동작'],
    ['사진', 'exifr, 브라우저 캔버스', '촬영 일시·GPS 읽기, 긴 변 1200px JPEG로 줄여 저장'],
    ['기기 저장', 'localStorage', '내 기록·북마크·알림·출석, 서버 전송 대기열'],
    ['서버', 'Cloudflare Workers, D1(SQLite)', '기록·사진 저장, 검수 후 공개, 전문가 검토, 오동정 제보, 북마크·조회수 집계'],
  ], { center: [0], boldCols: [0], fillCols: [0] }),
  gap(60),
  block('계획서 대비 구성 변경', [1300, 2300, 2700, 3566], ['구분', '계획서', '최종 결과물', '바꾼 이유'], [
    ['화면', 'Next.js·TypeScript 웹앱', 'HTML·CSS·JavaScript 단일 파일', '보안상 파일 교환이 불가해 연구소가 보고 재구현하는 시연물이 됨 → 빌드 없이 바로 열리는 형태'],
    ['설치', 'PWA(설치형)', '설치 없는 웹', '발표 현장에서 QR로 바로 사용. 설치가 필요한 아이폰 푸시는 앱 안 알림으로 대체'],
    ['인증·저장', 'Firebase 인증·저장', '기기 저장 + 시연용 서버, 닉네임·전문가 키', '기존 회원 시스템과 연동할 수 없어 시민·전문가 역할만 구분하고 공개 규칙은 서버에서 검사'],
    ['배포', 'Vercel', 'Cloudflare', '무료 범위에서 앱과 서버를 한 주소로 제공, 저장소 비공개 상태로도 배포 가능'],
  ], { center: [0], boldCols: [0], fillCols: [0] }),
  gap(40),
  note('구성은 바뀌었지만 계획서의 기능 목표(동정 진행 상태, 정렬·종별 모아보기, 생태지도, 포인트·배지·미션·랭킹, 탐험 리포트)는 모두 구현했습니다. 기존 앱의 기술 구조를 알 수 없어 운영 앱에 특정 기술을 권하지 않습니다.'),
  gap(40),
  block('공개와 보호 규칙 (서버에서 적용)', [W], null, [[[
    '· 공개 승인 전의 기록과 사진은 올린 기기와 전문가·관리자에게만 보내며, 다른 사람에게는 사진 자체를 보내지 않습니다.',
    '· 정확한 좌표는 올린 기기와 전문가·관리자에게만 보내고, 다른 사람에게는 소수 둘째 자리(약 1km)로 낮춰 보냅니다.',
    '· 기기당 하루 등록 30건·제보 20건, 사진 크기, 글자 수, 제주 밖 좌표를 서버에서 검사합니다. 검토·공개 처리는 전문가 키가 있어야 합니다.',
  ]]]),
  gap(60),
  note('운영 앱 반영을 위해 상태 흐름·데이터 항목·처리 규칙을 기능 단위의 명세로 정리했습니다.'),

  ...chapter(3, '실행 방법', true),
  block(null, [2000, 7866], ['상황', '방법'], [
    ['휴대폰·PC에서 실행', `${URL_} 에 접속하거나 발표 화면의 QR을 찍습니다. 설치가 필요 없으며, PC에서는 화면 높이에 맞춘 휴대폰 비율로 보입니다.`],
    ['기존/개선 비교', '화면 맨 위의 ‘기존 앱 | 개선 앱’ 버튼을 누르면 보고 있던 화면에서 바로 바뀝니다.'],
    ['전문가 동정 시연', '설정 → 전문가·관리자 로그인 → 전문가 키 입력(별도 전달). 전문가 검토 화면에서 공개 승인·비공개·삭제, 동정 상태·생물종·의견 저장, 오동정 제보 처리를 합니다. 결과는 올린 사람의 앱에 알림으로 전해집니다.'],
    ['오프라인 확인', '비행기 모드에서 기록을 등록하면 ‘서버 전송 대기’로 표시되고, 다시 연결되면 자동으로 올라갑니다.'],
    ['소스로 실행', 'JEJU_CIS_최종.html 파일 하나를 브라우저로 열면 동작합니다(서버 기능은 인터넷 연결 시). 서버는 배포 폴더에서 npx wrangler deploy로 다시 배포합니다.'],
  ], { boldCols: [0], fillCols: [0], center: [0] }),
  gap(100),
  block('검증 결과', [5933, 3933], ['검사', '결과'], [
    ['서버 권한·공개 규칙 API 검사', '28 / 28 통과'],
    ['실제 주소 종단 검사 (기기 2대: 등록 → 승인 → 알림 → 공개 → 오프라인 동기화 → 제보·북마크, 내 주변 표시, 삭제·입력 거르기)', '48 / 48 통과'],
    ['실기기 확인 (아이폰)', '정상 동작'],
    ['전체 화면 회귀 검사 (기존·개선 모드 60개 화면)', '오류 0건'],
    ['파일 크기', '1.5MB (전송 시 압축 약 0.5MB)'],
  ], { center: [1] }),
  gap(60),
  note('자동 검사는 헤드리스 브라우저로 실제 배포 주소에서 했고, 아이폰 실기기에서도 동작을 확인했습니다.'),
];

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: SZ } } } },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 850, bottom: 850, left: MARGIN, right: MARGIN, footer: 400 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: '- ', font: FONT, size: 18 }), new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 18 }), new TextRun({ text: ' -', font: FONT, size: 18 })] })] }) },
    children: body,
  }],
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync(OUT, b); console.log('ok', OUT, b.length); });
