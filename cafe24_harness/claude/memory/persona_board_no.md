---
name: persona_board_no
description: "이 몰의 리뷰 게시판 번호(board_no) — __FILL__. cf open boards로 확인 후 채울 것"
metadata:
  type: project
---

이 몰의 리뷰 게시판 번호: **__FILL__** (예: 4).

> 페르소나 플레이스홀더. 작업하며 채운다.

**채우는 법:**
- `cf open boards`로 게시판 목록을 보고 어느 게 후기 게시판인지 판단.
- `cf inspect board --board <N>` 하면 `admin/config.yaml`에 `board_no`가 자동 기록되고, 이 메모리의 `__FILL__`도 그 번호로 갱신.

**왜 중요:** 네이버페이 비회원 후기는 기본 "미게시"라 board_no를 알아야 `cf inspect board`로 미게시 글을 진단할 수 있다. 관련 [[feedback_cafe24_admin_no_bypass]].
