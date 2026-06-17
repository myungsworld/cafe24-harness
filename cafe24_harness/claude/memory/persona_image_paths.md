---
name: persona_image_paths
description: "이 몰의 이미지 업로드 위치 & HTML src 경로 컨벤션 — weskin 번호 __FILL__. /web/upload/<폴더>/ 사용, 로컬 레포 경로 금지"
metadata:
  type: project
---

카페24가 실제 서빙하는 이미지 경로는 **`/web/upload/<폴더>/...`** 형식. 이 몰의 기본 스킨 이미지 폴더(weskin 번호): **__FILL__** (예: `weskin60`).

> 페르소나 플레이스홀더. 다른 이미지의 `src`를 grep해서 실제 사용 경로를 확인한 뒤 채운다(추측 금지).

| 종류 | 카페24 업로드 위치 | HTML `src` |
|---|---|---|
| 기본 스킨 이미지 | `/web/upload/__FILL__/kr/main/` 등 | 동일 경로 |
| 신규 직접 업로드(로고/배너) | 사용자 지정 폴더 (예: `/web/upload/logo/`) | 동일 경로 |

**절대 하지 말 것:**
- 로컬 레포 경로(`/weskin_import/img/...`, `/skin*/weskin_import/img/...`)를 HTML `src`로 쓰지 않기 → 라이브 404 → `<img alt>` 텍스트 노출.
- weskin 번호를 추측하지 말 것 — 기존 이미지 `src`를 grep해 실제 경로 확인.

**작업 흐름:** 새 이미지 추가 시 ① 카페24 어느 경로에 업로드할지 사용자 확인 → ② `src`/`url()`을 그 경로로 → ③ 라이브 DevTools Network에서 200 확인(`/cafe24/echeck`) → 404면 경로 재확인.
