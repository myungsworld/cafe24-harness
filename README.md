# cafe24-harness

포터블 **카페24 어드민 자기개선 하네스**. 카페24 관리자 화면을 Playwright로 직접 열어 문제를 눈으로 확인하고, 셀렉터/지식을 그때그때 보정하는 도구. 모든 카페24 몰이 공통이므로 코어는 이 패키지에 모으고, 프로젝트엔 몰 도메인/board_no 같은 설정만 둔다.

## 설치 (전역)

```sh
pipx install git+https://github.com/myungsworld/cafe24-harness
cf setup        # 최초 1회: chromium 설치
```

(하네스 자체를 개발할 때의 로컬 설치는 [AGENTS.md](AGENTS.md) 참조.)

## 사용

```sh
cd <카페24 프로젝트>
cf init             # 대화형: 몰 도메인 / 게시판 번호 입력 → ./admin/ 설정 + 훅 등록 (멱등)
cf login            # headed 브라우저 → 직접 로그인 → 세션 저장
cf inspect board    # 게시물 관리 진단(미게시 글 감지) — 읽기전용
cf doctor           # 세션/설정/크로미움 점검
```

`cf init` 한 방이면 설정 + SessionStart 훅까지 끝난다(멱등).
비대화형으로 넣으려면: `cf init --mall yourmall.cafe24.com --board 4` (훅 빼려면 `--no-hook`).

## 자동 업그레이드 (거버넌스 전파)

**cf init 된 프로젝트에서 Claude 세션을 열 때마다** 자동으로 최신 하네스를 당겨온다. 훅은 `cf init`이 자동 등록한다.

- 동작: 세션 시작 → `admin/config.yaml` 있는 프로젝트면 → `cf upgrade`(쿨다운 6h)를 백그라운드 실행. 비차단·실패무시.
- 수동: `cf upgrade` (지금 바로) / `cf hook install`·`cf hook uninstall` (재설치·해제)
- 전제: GitHub에서 `pipx install git+...`로 설치돼 있어야 실제로 최신 커밋을 당겨온다.

> 흐름: `~/cafe24-harness` 고치고 push → 각 프로젝트가 다음 세션에서 `cf upgrade`로 자동 반영.

## 메인테이너

이 레포를 고치는 규칙은 [AGENTS.md](AGENTS.md) 참조. 핵심: **거버넌스/동작/명령이 바뀌면 같은 커밋에서 README와 knowledge를 반드시 동기화하고 version을 올린다.**

## 원칙

- **로그인은 사람이** headed 브라우저에서 직접 (자동 크리덴셜 저장 안 함).
- **세션(`secrets/*.json`)·캡쳐는 프로젝트별, gitignore.** 공유 레포에 절대 커밋 금지.
- **읽기전용 우선**: `inspect`는 진단만. 라이브 상태 변경(게시 토글 등) 자동화하지 않음 — 관리자 설정은 코드로 우회하지 않는다.
- 셀렉터는 코드 밖(YAML). 카페24 동작 지식은 `cafe24_harness/knowledge/`.

## 구조

```
cafe24_harness/
├── cli.py            # cf init|login|inspect|setup|doctor
├── config.py         # 프로젝트 config.yaml 로드 + URL 해석
├── urls.py           # 카페24 공통 URL 템플릿
├── browser.py        # Playwright 컨텍스트/세션/페이지 덤프
├── commands/         # 각 서브커맨드 구현
├── templates/        # cf init 이 프로젝트에 쓰는 파일
└── knowledge/        # 카페24 어드민 거버넌스(공유 지식)
```

프로젝트 풋프린트(`cf init` 후):

```
admin/
├── config.yaml                  # mall_domain / shop_id / board_no
├── selectors/cafe24_board.yaml  # target_reviews / writer_keyword / status_keywords
├── secrets/   (gitignore, 세션)
└── screenshots/ (gitignore, 캡쳐)
```
