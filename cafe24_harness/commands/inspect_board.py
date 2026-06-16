"""cf inspect board — 게시물 관리 화면 진단 (미게시 글 감지). 읽기전용."""
from __future__ import annotations

import time

from .. import browser
from ..config import ProjectConfig, resolve_admin_dir


def run(args) -> int:
    cfg = ProjectConfig.load(resolve_admin_dir(args.dir))
    if not cfg.is_configured():
        print("⚠️ config.yaml 의 mall_domain 미설정. `cf init --mall <도메인>` 먼저.")
        return 1
    if not cfg.has_session():
        print(f"⚠️ 저장된 세션 없음({cfg.state_file}). 먼저: cf login")
        return 1

    selectors = cfg.load_selectors()
    headed = getattr(args, "headed", False)
    url = getattr(args, "url", None) or cfg.board_list_url()
    dash = cfg.dashboard_url()

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b, context, page = browser.new_context(p, cfg, headless=not headed, use_state=True)
        # 레거시 php는 referer 없으면 403 → 대시보드 먼저 경유
        try:
            page.goto(dash, wait_until="domcontentloaded", timeout=30000)
            time.sleep(1.5)
        except Exception as e:
            print(f"(대시보드 경유 경고) {e}")
        try:
            page.goto(url, referer=dash, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"(이동 경고) {e}")
        time.sleep(3)  # 어드민 iframe/JS 로딩 대기

        if "eclogin" in page.url.lower():
            print(f"⚠️ 세션 만료로 로그인 페이지로 튕김: {page.url}\n   다시: cf login")
            browser.shot(cfg, page, "session_expired")
            b.close()
            return 1

        report = browser.dump_page(cfg, page, selectors, f"inspect_board_{cfg.board_no}")

        # 미게시(게시함 버튼 = ePostId_) 글번호 추출 — 스토어프론트 미노출의 원인
        unpub = []
        for fr in page.frames:
            try:
                ids = fr.eval_on_selector_all(
                    "a[id^='ePostId_']",
                    "els => els.map(e => e.id.replace('ePostId_',''))",
                )
                unpub.extend(ids)
            except Exception:
                pass
        unpub = sorted(set(unpub), key=lambda x: -int(x) if x.isdigit() else 0)

        browser.print_summary(report)
        print("\n" + "=" * 60)
        print(f"🚫 미게시(게시함 버튼 있음) 글번호 {len(unpub)}개: {unpub}")
        print("   → 이 글들은 스토어프론트 게시판/메인에 노출 안 됨.")
        print("   → 게시물 관리에서 각 글 '게시함' 버튼 클릭(게시 처리)해야 노출됨.")
        b.close()
    return 0
