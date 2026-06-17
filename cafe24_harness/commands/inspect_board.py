"""cf inspect board — 게시물 관리 화면의 미게시 글 진단 (제네릭 카페24 기능). 읽기전용.

게시판 번호(board_no)는 추측하지 않는다 — 그건 그 몰의 페르소나다.
  --board N  >  프로젝트 config.yaml 의 board_no(페르소나)  >  (없으면 에러)
--board 로 처음 지정하면 config.yaml 에 페르소나로 기록되어 다음부터 자동.
'어느 게시판이 후기인지'는 `cf open boards` 로 직접 보고 판단해서 지정한다.
"""
from __future__ import annotations

import time

from .. import browser
from ..config import ProjectConfig, resolve_admin_dir


def run(args) -> int:
    cfg = ProjectConfig.load(resolve_admin_dir(args.dir))
    if not cfg.is_configured():
        print("⚠️ config.yaml 의 mall_domain 미설정. `cf init` 먼저.")
        return 1
    if not cfg.has_session():
        print(f"⚠️ 세션 없음({cfg.state_file}). 먼저: cf login")
        return 1

    explicit = getattr(args, "board", None)
    board = explicit or cfg.board_no
    if not board:
        print("⚠️ 이 프로젝트에 리뷰 게시판 번호(페르소나)가 없습니다.")
        print("   1) `cf open boards` 로 게시판 목록을 보고 후기 게시판 번호를 확인")
        print("   2) `cf inspect board --board <N>` 로 지정 (config.yaml 에 자동 기록됨)")
        return 1
    if explicit:
        cfg.remember_board(int(explicit))  # 페르소나로 저장
    cfg.board_no = int(board)

    selectors = cfg.load_selectors()  # 패키지 골격 + 프로젝트 override
    prefix = selectors.get("post_toggle_id_prefix", "ePostId_")
    headed = getattr(args, "headed", False)
    dash = cfg.dashboard_url()
    url = getattr(args, "url", None) or cfg.board_list_url()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b, context, page = browser.new_context(p, cfg, headless=not headed, use_state=True)
        try:
            page.goto(dash, wait_until="domcontentloaded", timeout=30000)
            time.sleep(1.5)
        except Exception as e:
            print(f"(대시보드 경유 경고) {e}")
        try:
            page.goto(url, referer=dash, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"(이동 경고) {e}")
        time.sleep(3)

        if "eclogin" in page.url.lower():
            print("⚠️ 세션 만료로 로그인 페이지로 튕김. 다시: cf login")
            browser.shot(cfg, page, "session_expired")
            b.close()
            return 1

        report = browser.dump_page(cfg, page, selectors, f"inspect_board_{cfg.board_no}")

        # 미게시(게시함 버튼) 글번호 — 골격의 prefix 사용
        unpub = []
        for fr in page.frames:
            try:
                ids = fr.eval_on_selector_all(
                    f"a[id^='{prefix}']",
                    f"els => els.map(e => e.id.replace('{prefix}',''))",
                )
                unpub.extend(ids)
            except Exception:
                pass
        unpub = sorted(set(unpub), key=lambda x: -int(x) if x.isdigit() else 0)

        browser.print_summary(report)
        print("\n" + "=" * 60)
        print(f"게시판 board_no={cfg.board_no}")
        print(f"🚫 미게시(게시함 버튼 있음) 글번호 {len(unpub)}개: {unpub}")
        print("   → 스토어프론트 미노출. 게시물 관리에서 '게시함' 클릭해야 노출됨.")
        b.close()
    return 0
