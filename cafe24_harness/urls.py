"""카페24 공통 어드민 URL 템플릿 (공유 지식).

모든 카페24 몰이 동일한 경로 구조를 쓰고, 몰 도메인 / shop_id / board_no 만 다르다.
신관리자(disp/admin SPA)와 레거시 php 페이지가 공존하며, 레거시는 referer 없이
직접 접근하면 403 → 대시보드 경유가 필요하다(browser.dump 흐름에서 처리).
"""
from __future__ import annotations

SHOP_DEFAULT = "shop1"


def login_url(mall: str, shop: str = SHOP_DEFAULT) -> str:
    # eclogin SSO로 리다이렉트되는 관리자 진입점
    return f"https://{mall}/admin"


def dashboard_url(mall: str, shop: str = SHOP_DEFAULT) -> str:
    return f"https://{mall}/disp/admin/{shop}/main/dashboard"


def board_list_url(mall: str, shop: str, board_no: int) -> str:
    # 게시물 관리 (글 목록 + 글고정 + 게시/미게시 토글)
    return (
        f"https://{mall}/admin/php/{shop}/b/"
        f"board_admin_bulletin_l.php?board_no={board_no}"
    )


def board_setting_url(mall: str, shop: str, board_no: int) -> str:
    # 게시판 관리(게시판 설정)
    return (
        f"https://{mall}/admin/php/{shop}/b/"
        f"board_admin_l.php?board_no={board_no}"
    )
