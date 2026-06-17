# AGENTS.md — cafe24-harness 메인테이너 가이드

이 레포는 카페24 어드민 하네스다. 여기를 고치면 각 프로젝트의 SessionStart 훅이 `cf upgrade`로 당겨가
**모든 카페24 프로젝트에 전파**된다. 따라서 변경은 항상 일관되게, 문서와 함께 가야 한다.

## 지식 3층 구조 (핵심 원칙)

- **골격/공통지식 = 패키지 소유, 모든 몰 공통.** `skeletons/` 셀렉터 + `knowledge/` 동작지식 + 코드의 URL/폼 구조 + `claude/memory/feedback/` 작업습관.
  예: "미게시 글은 게시함(`ePostId_`) 버튼 눌러야 노출", 메인진열 표시설정은 관리자 영역(코드 우회 금지), 게시물 관리 URL 패턴.
- **페르소나(persona) = 프로젝트 소유, 그 몰 고유.** 프로젝트 `admin/config.yaml` + 자동 로드 메모리 `persona_*.md`(시드 플레이스홀더 `__FILL__`).
  예: "이 몰의 리뷰 게시판 = 4번", weskin 이미지 경로, 스킨 "대표 디자인". `cf inspect board --board N` 하면 config 에 자동 기록된다.
- **도구는 판단하지 않는다.** "이 몰에선 뭐가 후기냐" 같은 건 코드에 박지 말 것(키워드 추측·기본값 금지).
  에이전트가 `cf open`으로 보고 판단해서 페르소나에 기록한다. **기능 들어올 때마다 박지 말 것.**
- **골격 자가수정**: Playwright 실행 중 어드민 폼/UI가 바뀌어 셀렉터가 깨지면, `skeletons/`(또는 knowledge)를
  고쳐서 패키지를 업데이트한다 → push → 전 프로젝트 전파. (페르소나는 안 건드림)
- **승격(promote)**: 작업 중 발견한 "모든 몰 공통" 지식은 `knowledge/`(또는 `claude/memory/feedback/`)로 올려 전파.
  그 몰 고유면 페르소나로 남긴다.

## Claude Code 자산 (commands/agents/memory)

- `claude/` 의 슬래시 명령어·에이전트·메모리 시드는 **패키지 데이터**로 배포된다(`pyproject.toml` package-data 에 `claude/**/*` 포함 필수 — 빠지면 wheel 에서 누락).
- `cf claude install` 이 `~/.claude/commands/cafe24/`·`~/.claude/agents/`로 **복사**(심링크 아님 — pipx venv 는 재설치 때 경로가 바뀜). `cf init` 이 자동 호출, `cf upgrade` 후처리가 갱신 → **CLI 와 같은 단일 채널 전파.**
- 메모리 시드는 `cf init` 이 **Claude 자동 로드 메모리 디렉토리**(`~/.claude/projects/<프로젝트경로 '/'·'.'→'-' 인코딩>/memory/`)로 머지(멱등, 기존 파일·페르소나 보존). MEMORY.md 는 줄 단위 머지. 레포 안에 넣지 않는 이유: Claude 가 자동 로드하는 위치가 거기라서. 씨앗은 패키지에 있어 `cf upgrade`로 전파.
- **기성 프로젝트 보호**: 그 프로젝트 메모리 디렉토리에 (MEMORY.md 외) 파일이 이미 있으면 시드를 **건너뛴다**. 시드는 새 프로젝트용 씨앗이고 메모리는 healic→새 프로젝트 방향으로만 흐른다(시드의 추출 원본인 healic 이 항상 앞섬). 강제: `cf init --seed-memory`.
- **읽기전용 원칙은 명령어에도 적용**: `/cafe24/work admin`·`/cafe24/echeck` 의 어드민 단계는 진단·안내만. 게시 토글(`setPost`) 등 라이브 변경은 사용자 승인 후 수동.

## 🔴 거버넌스 변경 시 필수 (같은 커밋에서)

명령/플래그/동작/구조를 바꾸면 — **반드시 같은 커밋에서 함께** 수정한다:

1. **README.md** — 사용자 진실의 원천. 명령/사용법/동작이 바뀌면 README가 항상 그에 맞아야 한다.
2. **cafe24_harness/knowledge/cafe24_admin.md** — 카페24 동작 지식을 발견/수정했으면 갱신.
3. **Claude 자산 동기화** — `claude/commands|agents|memory` 를 추가/변경하면 `pyproject.toml` package-data(`claude/**/*`)에 포함됐는지 확인하고 README 표를 맞춘다.
4. **버전 bump** — `cafe24_harness/__init__.py` 의 `__version__` + `pyproject.toml` 의 `version`.
5. push → 각 프로젝트가 다음 세션에서 `cf upgrade`로 자동 반영(코드 + 슬래시 명령어 + 에이전트 + 지식).

> README와 코드가 어긋나면 거버넌스가 깨진 것으로 본다. "동작을 바꿨는데 README는 그대로"는 금지.

## 원칙

- **읽기전용 우선**: `inspect` 등 진단만 자동화. 라이브 상태 변경(게시 토글 등)은 자동화하지 않는다.
  관리자에서 풀리는 문제를 코드로 우회하지 않는다.
- **멱등**: `cf init`, `cf hook install`은 여러 번 실행해도 안전(중복 생성 금지).
- **세션 쿠키/캡쳐는 프로젝트별·gitignore.** 이 레포에 절대 커밋 금지.
- **로그인은 사람이** headed 브라우저에서 직접. 자동 크리덴셜 저장 금지.
- 셀렉터는 코드 밖(프로젝트 selectors YAML). 카페24 공통 지식은 `knowledge/`.

## 구조

```
cafe24_harness/
├── cli.py        # cf init|login|open|inspect|doctor|setup|upgrade|hook|claude
├── config.py     # 프로젝트 config.yaml 로드 + URL 해석
├── urls.py       # 카페24 공통 URL 템플릿
├── browser.py    # Playwright 컨텍스트/세션/덤프
├── commands/     # 서브커맨드 구현 (init/login/inspect_board/doctor/upgrade/hook/claude)
├── templates/    # cf init 산출물 + hooks/cafe24-session-start.sh
├── knowledge/    # 카페24 어드민 거버넌스(공유 지식)
└── claude/       # Claude Code 자산 — cf claude install 이 ~/.claude 로 복사
    ├── commands/cafe24/   # /cafe24/work, /cafe24/echeck
    ├── agents/            # cafe24-planner, cafe24-evaluator
    └── memory/            # 포터블 메모리 시드 (feedback 작업습관 + persona 플레이스홀더)
```

## 릴리스/전파

- 로컬 개발: `pipx install --editable .`
- 배포 설치: `pipx install git+https://github.com/myungsworld/cafe24-harness`
- 전파: 변경 push → 프로젝트 SessionStart 훅이 `cf upgrade`(쿨다운 6h)로 당김.
