# 카페24 어드민 거버넌스 (공유 지식)

> 모든 카페24 몰에 공통으로 적용되는 동작·함정. 새 몰에서 같은 문제가 반복되므로 여기에 누적한다.
> 재발/신규 발견 시 이 문서를 고치면 `pipx upgrade` 로 전 프로젝트에 전파된다.

## URL 구조

- **로그인 진입점**: `https://{mall}/admin` → `eclogin.cafe24.com` SSO로 리다이렉트.
- **신관리자(SPA)**: `https://{mall}/disp/admin/{shop}/main/dashboard` 등 `disp/admin/{shop}/...`. shop은 보통 `shop1`.
- **레거시 PHP**: `https://{mall}/admin/php/{shop}/b/*.php` (게시판 등).
  - ⚠️ **referer 없이 직접 접근하면 403.** 대시보드를 먼저 연 뒤 referer를 달고 이동해야 열린다.
    (`cf inspect` 가 자동으로 대시보드 경유 처리)

## 게시판 (리뷰)

- **게시판 관리(설정)**: `board_admin_l.php?board_no=N`
- **게시물 관리(글 목록 + 글고정 + 게시/미게시)**: `board_admin_bulletin_l.php?board_no=N`
- **네이버페이(비회원) 후기는 기본 "미게시"**:
  - 회원 후기는 작성 즉시 게시 → 별도 버튼 없음.
  - 네이버페이/외부연동 후기는 게시물 관리에 `<a id="ePostId_{no}" onclick="setPost('{board}','{no}')">게시함</a>` 버튼이 붙음.
  - **버튼이 보이면 = 미게시(스토어프론트 미노출).** 클릭하면 게시 처리되고 버튼이 사라짐.
  - `setPost` → `/exec/admin/{shop}/board/PostAjax`.
  - 진단: `cf inspect board` 가 `ePostId_` 버튼을 스캔해 미게시 글번호를 출력.
- "공개/비공개" 컬럼은 없음 — 게시/미게시가 그 역할.

## 메인 리뷰 ≠ 게시판 (외부 위젯 주의)

- 메인페이지 리뷰는 카페24 게시판이 아니라 **외부 리뷰 솔루션(예: 크리마 Crema, cre.ma)** 위젯이 덮을 수 있다.
  - 크리마가 `.reviewSlide` 안에 `iframe#crema-reviews-1`(widget_id별)을 주입 → 카페24 게시글이 DOM엔 있어도 시각적으로 가려짐.
  - 증상: 게시/고정/캐시삭제 다 해도 메인 화면이 안 바뀜. curl/소스보기로는 게시글이 보이지만 그건 숨은 DOM.
  - 해결: 외부 위젯(크리마) 관리자에서 설정. 카페24 작업과 별개.
- **체크 습관**: 메인 리뷰가 안 바뀌면 `widgets.cre.ma` / `review*.cre.ma` 같은 외부 스크립트가 떠 있는지 먼저 확인.

## 원칙

- **읽기전용 우선**: 진단만 자동화. 라이브 상태 변경(`setPost` 등)은 사람이 승인 후 수동.
  관리자에서 풀리는 문제를 CSS/JS로 우회 구현하지 않는다.
- **로그인은 사람이** headed 브라우저에서 직접. 자동 크리덴셜 저장 금지.
- **세션 쿠키(`secrets/*.json`)·캡쳐는 프로젝트별, gitignore.** 공유 레포 커밋 금지.
