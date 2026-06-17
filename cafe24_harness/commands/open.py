"""cf open — 아무 카페24 어드민 페이지를 열어 DOM/스크린샷을 덤프 (제네릭, 읽기전용).

판단(어느 게 후기 게시판인지 등)은 이 도구가 하지 않는다. 에이전트가 덤프를 읽고 판단한다.

target:
  - 전체 URL (https://...)
  - 경로 (/admin/php/shop1/b/...) → 몰 도메인 자동 prefix
  - alias: dashboard | boards(게시판 관리 목록)
"""
from __future__ import annotations

import time

from .. import browser
from ..config import ProjectConfig, resolve_admin_dir


def _resolve_url(cfg, target: str) -> str:
    if target in ("dashboard", "dash"):
        return cfg.dashboard_url()
    if target in ("boards", "board-list"):
        return cfg.board_admin_list_url()
    if target.startswith("http"):
        return target
    if target.startswith("/"):
        return f"https://{cfg.mall_domain}{target}"
    return target


def run(args) -> int:
    cfg = ProjectConfig.load(resolve_admin_dir(args.dir))
    if not cfg.is_configured():
        print("⚠️ config.yaml 의 mall_domain 미설정. `cf init` 먼저.")
        return 1
    if not cfg.has_session():
        print(f"⚠️ 세션 없음({cfg.state_file}). 먼저: cf login")
        return 1

    url = _resolve_url(cfg, args.target)
    dash = cfg.dashboard_url()
    headed = getattr(args, "headed", False)
    use_referer = not getattr(args, "no_referer", False)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        b, context, page = browser.new_context(p, cfg, headless=not headed, use_state=True)
        # 레거시 php는 referer 없으면 403 → 대시보드 먼저 경유
        if use_referer and url != dash:
            try:
                page.goto(dash, wait_until="domcontentloaded", timeout=30000)
                time.sleep(1.2)
            except Exception as e:
                print(f"(대시보드 경유 경고) {e}")
        try:
            page.goto(url, referer=dash if use_referer else None, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"(이동 경고) {e}")
        time.sleep(3)

        if "eclogin" in page.url.lower():
            print("⚠️ 세션 만료로 로그인 페이지로 튕김. 다시: cf login")
            browser.shot(cfg, page, "session_expired")
            b.close()
            return 1

        report = browser.dump_raw(cfg, page, "open")
        browser.print_raw_summary(report)
        b.close()
    return 0
