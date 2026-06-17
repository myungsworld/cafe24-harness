# AGENTS.md — cafe24-harness 메인테이너 가이드

이 레포는 카페24 어드민 하네스다. 여기를 고치면 각 프로젝트의 SessionStart 훅이 `cf upgrade`로 당겨가
**모든 카페24 프로젝트에 전파**된다. 따라서 변경은 항상 일관되게, 문서와 함께 가야 한다.

## 지식 2층 구조 (핵심 원칙)

- **골격(skeleton) = 패키지 소유, 모든 몰 공통.** `skeletons/` 의 셀렉터 + `knowledge/` 의 동작지식 + 코드의 URL/폼 구조.
  예: "미게시 글은 게시함(`ePostId_`) 버튼 눌러야 노출", 게시물 관리 URL 패턴, 테이블 구조.
- **페르소나(persona) = 프로젝트 소유, 그 몰 고유.** 프로젝트 `admin/config.yaml`.
  예: "이 몰의 리뷰 게시판 = 4번". `cf inspect board --board N` 하면 여기에 자동 기록된다.
- **도구는 판단하지 않는다.** "이 몰에선 뭐가 후기냐" 같은 건 코드에 박지 말 것(키워드 추측·기본값 금지).
  에이전트가 `cf open`으로 보고 판단해서 페르소나에 기록한다. **기능 들어올 때마다 박지 말 것.**
- **골격 자가수정**: Playwright 실행 중 어드민 폼/UI가 바뀌어 셀렉터가 깨지면, `skeletons/`(또는 knowledge)를
  고쳐서 패키지를 업데이트한다 → push → 전 프로젝트 전파. (페르소나는 안 건드림)

## 🔴 거버넌스 변경 시 필수 (같은 커밋에서)

명령/플래그/동작/구조를 바꾸면 — **반드시 같은 커밋에서 함께** 수정한다:

1. **README.md** — 사용자 진실의 원천. 명령/사용법/동작이 바뀌면 README가 항상 그에 맞아야 한다.
2. **cafe24_harness/knowledge/cafe24_admin.md** — 카페24 동작 지식을 발견/수정했으면 갱신.
3. **버전 bump** — `cafe24_harness/__init__.py` 의 `__version__` + `pyproject.toml` 의 `version`.
4. push → 각 프로젝트가 다음 세션에서 `cf upgrade`로 자동 반영.

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
├── cli.py        # cf init|login|inspect|doctor|setup|upgrade|hook
├── config.py     # 프로젝트 config.yaml 로드 + URL 해석
├── urls.py       # 카페24 공통 URL 템플릿
├── browser.py    # Playwright 컨텍스트/세션/덤프
├── commands/     # 서브커맨드 구현 (init/login/inspect_board/doctor/upgrade/hook)
├── templates/    # cf init 산출물 + hooks/cafe24-session-start.sh
└── knowledge/    # 카페24 어드민 거버넌스(공유 지식)
```

## 릴리스/전파

- 로컬 개발: `pipx install --editable .`
- 배포 설치: `pipx install git+https://github.com/myungsworld/cafe24-harness`
- 전파: 변경 push → 프로젝트 SessionStart 훅이 `cf upgrade`(쿨다운 6h)로 당김.
