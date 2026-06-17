# cafe24-harness

포터블 **카페24 어드민 자기개선 하네스**. 카페24 관리자 화면을 Playwright로 직접 열어 문제를 눈으로 확인하고, 셀렉터/지식을 그때그때 보정하는 도구. 모든 카페24 몰이 공통이므로 코어는 이 패키지에 모으고, 프로젝트엔 몰 도메인/board_no 같은 설정만 둔다.

## 설치 (전역)

```sh
pipx install git+https://github.com/myungsworld/cafe24-harness
cf setup        # 최초 1회: chromium 설치
```

(하네스 자체를 개발할 때의 로컬 설치는 [AGENTS.md](AGENTS.md) 참조.)

## 지식 구조 (골격 ↔ 페르소나)

| 층 | 위치 | 내용 |
|---|---|---|
| **골격(skeleton)** | 패키지 `cafe24_harness/skeletons/` + `knowledge/` | 모든 몰 공통 — 어드민 폼 구조, "미게시 글은 게시함(ePostId_) 버튼 눌러야 노출", URL 패턴 등. 어드민 UI가 바뀌면 여기를 고쳐 업데이트. |
| **페르소나(persona)** | 프로젝트 `admin/config.yaml` | 그 몰 고유값 — 몰 도메인, "리뷰 게시판 = 4번" 등. 작업하며 채워지고, 다음부턴 빠르게. |

> 여기에 더해 Claude Code 작업용 **메모리/지식 3층**(공통지식 · 작업습관 · 몰별 페르소나)이 있다 — 아래 [Claude Code 통합 → 포터블 메모리](#포터블-메모리-3층) 참조.

`cf`는 **제네릭한 어드민 접근 도구**다. "이 몰에선 뭐가 후기냐" 같은 판단은 도구가 박지 않는다 — 사람/에이전트가 `cf open`으로 보고 판단해 페르소나에 기록한다.

## 사용

```sh
cd <카페24 프로젝트>
cf init                       # 대화형: 몰 도메인만 입력 → admin/ 페르소나 + Claude 자산/메모리 + 훅 (멱등)
cf login                      # headed 브라우저 → 직접 로그인 → 세션 저장
cf open boards                # 게시판 목록을 열어 DOM/스샷 덤프 → 어느 게 후기인지 보고 판단
cf inspect board --board 4    # 그 번호로 미게시 글 진단 (config에 페르소나 자동 기록)
cf inspect board              # 이후엔 기록된 번호로 바로
cf open <url|/path|alias>     # 아무 어드민 페이지나 열어 덤프 (제네릭)
cf doctor                     # 세션/설정/크로미움 점검
```

비대화형: `cf init --mall yourmall.cafe24.com` (훅 빼려면 `--no-hook`).

## Claude Code 통합 (슬래시 명령어 · 에이전트 · 메모리)

`cf`(CLI)에 더해, 카페24 작업용 **Claude Code 슬래시 명령어 + 에이전트 + 포터블 메모리**를 같이 배포한다. `cf init`(또는 `cf claude install`)이 `~/.claude/`로 복사하고, `cf upgrade`가 갱신한다 — **CLI와 같은 단일 채널로 전파.**

```sh
cf claude install            # ~/.claude/commands/cafe24/ + agents/ 설치·갱신 (멱등)
```

| 자산 | 무엇 |
|---|---|
| `/cafe24/work` | plan→do→check **+ admin** 워크플로. "코드 고쳤는데 화면이 안 바뀜"을 **어드민 설정 문제로 진단**(`cf inspect`/`cf open` 연동). |
| `/cafe24/echeck` | 라이브 검수. **스토어프론트 DOM + 어드민 상태 교차검증** → 원인을 [코드/어드민설정/외부위젯]으로 판정. |
| 에이전트 `cafe24-planner` | 작업을 [코드] vs [어드민 설정]으로 분류해 분해. |
| 에이전트 `cafe24-evaluator` | 코드 QA + Playwright + 어드민 상태 검증. |

### 포터블 메모리 (3층)

`cf init` 이 **Claude 가 세션 시작 때 자동 로드하는 메모리 디렉토리**(`~/.claude/projects/<프로젝트경로>/memory/`)로 누적 지혜를 시드한다(멱등, 기존 메모리·MEMORY.md 보존):

- **공통 지식** (`knowledge/cafe24_admin.md`, 전파됨) — 모든 몰 공통 함정(미게시 후기, 크리마 위젯, 메인진열 표시설정 등).
- **작업습관 feedback** (시드, 전파) — 상세 코드설명, 명시적 커밋, client-report 포맷, 관리자 설정 코드우회 금지 등.
- **몰별 persona** (시드 플레이스홀더 `__FILL__`) — board_no, weskin 이미지 경로, 스킨 "대표 디자인". 작업하며 채운다.

> 시드 *씨앗*은 하네스 패키지(`claude/memory/`)에 살며 `cf upgrade`로 갱신·전파된다. 실제로 깔린 메모리는 머신 로컬이지만, 어느 머신이든 하네스 깔고 `cf init` 하면 첫 세션부터 누적 지혜가 자동 로드된다 — **포터블함은 레포가 아니라 하네스에 산다.**
>
> **기성 프로젝트 보호**: 그 프로젝트에 이미 메모리가 있으면 `cf init`은 시드를 **건너뛴다**(기존 메모리가 시드보다 풍부할 수 있으므로 — 시드는 사실 그런 프로젝트에서 추출한 것). 빈칸 페르소나(`__FILL__`)로 덮어 클러터를 만들지 않는다. 굳이 누락 시드를 채우려면 `cf init --seed-memory`.

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
├── cli.py        # cf init|login|open|inspect|doctor|setup|upgrade|hook|claude
├── config.py     # 페르소나 로드 + URL 해석 + 골격 병합
├── urls.py       # 카페24 공통 URL 템플릿
├── browser.py    # Playwright 컨텍스트/세션 + 덤프(dump_page/dump_raw)
├── commands/     # 서브커맨드 구현 (claude.py = Claude 자산 설치/메모리 시드)
├── skeletons/    # 공통 골격(셀렉터) — 모든 몰 공통
├── templates/    # cf init 산출물 + hooks 스크립트
├── knowledge/    # 카페24 어드민 거버넌스(공유 지식)
└── claude/       # Claude Code 자산 (cf 가 ~/.claude 로 복사)
    ├── commands/cafe24/   # /cafe24/work, /cafe24/echeck
    ├── agents/            # cafe24-planner, cafe24-evaluator
    └── memory/            # 포터블 메모리 시드 (feedback + persona)
```

프로젝트 풋프린트(`cf init` 후) — **페르소나만**:

```
admin/
├── config.yaml      # mall_domain [+ board_no 등 그 몰 고유값]
├── secrets/         # 세션 (gitignore)
└── screenshots/     # 캡쳐/덤프 (gitignore)
# selectors/ 는 그 몰 어드민이 골격과 다를 때만 override용으로 생성
```

> 메모리는 레포 안이 아니라 **Claude 자동 로드 위치**(`~/.claude/projects/<프로젝트경로>/memory/`)에 시드된다 — 위 [포터블 메모리](#포터블-메모리-3층) 참조. 슬래시 명령어·에이전트는 전역 `~/.claude/`(프로젝트 무관).
