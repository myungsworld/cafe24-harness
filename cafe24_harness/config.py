"""프로젝트 설정(페르소나) 로드 + 경로/URL 해석 + 공통 골격(skeleton) 병합.

- 공통 골격(selectors)은 패키지(cafe24_harness/skeletons/)에 있다 — 모든 몰 공통.
- 프로젝트(admin/)에는 페르소나만: config.yaml(mall/board) + (선택) selectors override.
"""
from __future__ import annotations

import re
from importlib import resources
from pathlib import Path

import yaml

from . import urls

CONFIG_NAME = "config.yaml"
PLACEHOLDER_MALL = "__MALL__"


def resolve_admin_dir(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    cwd = Path.cwd()
    if (cwd / "admin" / CONFIG_NAME).exists():
        return (cwd / "admin").resolve()
    if (cwd / CONFIG_NAME).exists():
        return cwd.resolve()
    return (cwd / "admin").resolve()


def _skeleton(name: str) -> dict:
    try:
        txt = (resources.files("cafe24_harness") / "skeletons" / f"{name}.yaml").read_text(encoding="utf-8")
        return yaml.safe_load(txt) or {}
    except Exception:
        return {}


class ProjectConfig:
    def __init__(self, admin_dir: Path):
        self.dir = Path(admin_dir).resolve()
        self.config_path = self.dir / CONFIG_NAME
        self.mall_domain = PLACEHOLDER_MALL
        self.shop_id = urls.SHOP_DEFAULT
        self.board_no = None  # 페르소나 — 없으면 None (패키지 기본값 안 둠)
        self.secrets = self.dir / "secrets"
        self.screenshots = self.dir / "screenshots"
        self.selectors_dir = self.dir / "selectors"
        self.state_file = self.secrets / "cafe24_state.json"

    @classmethod
    def load(cls, admin_dir: Path) -> "ProjectConfig":
        cfg = cls(admin_dir)
        if not cfg.config_path.exists():
            raise FileNotFoundError(
                f"설정이 없습니다: {cfg.config_path}\n  먼저 `cf init` 을 실행하세요."
            )
        data = yaml.safe_load(cfg.config_path.read_text(encoding="utf-8")) or {}
        cfg.mall_domain = data.get("mall_domain", PLACEHOLDER_MALL)
        cfg.shop_id = data.get("shop_id", urls.SHOP_DEFAULT)
        cfg.board_no = data.get("board_no")
        return cfg

    # --- 상태 ---
    def is_configured(self) -> bool:
        return bool(self.mall_domain) and self.mall_domain != PLACEHOLDER_MALL

    def has_session(self) -> bool:
        return self.state_file.exists()

    # --- URL (urls 템플릿으로 계산) ---
    def login_url(self) -> str:
        return urls.login_url(self.mall_domain, self.shop_id)

    def dashboard_url(self) -> str:
        return urls.dashboard_url(self.mall_domain, self.shop_id)

    def board_admin_list_url(self) -> str:
        return urls.board_admin_list_url(self.mall_domain, self.shop_id)

    def board_list_url(self) -> str:
        return urls.board_list_url(self.mall_domain, self.shop_id, self.board_no)

    def board_setting_url(self) -> str:
        return urls.board_setting_url(self.mall_domain, self.shop_id, self.board_no)

    # --- 셀렉터: 패키지 골격 + 프로젝트 override ---
    def load_selectors(self, name: str = "cafe24_board") -> dict:
        merged = dict(_skeleton(name))
        p = self.selectors_dir / f"{name}.yaml"
        if p.exists():
            proj = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            merged.update(proj)
        return merged

    # --- 페르소나 기록: board_no 를 config.yaml 에 멱등 추가 ---
    def remember_board(self, board_no: int) -> None:
        txt = self.config_path.read_text(encoding="utf-8") if self.config_path.exists() else ""
        if re.search(r"^\s*board_no\s*:", txt, re.M):
            return  # 이미 있음
        if txt and not txt.endswith("\n"):
            txt += "\n"
        txt += f"board_no: {board_no}   # 페르소나: 이 몰의 리뷰 게시판 번호\n"
        self.config_path.write_text(txt, encoding="utf-8")
        self.board_no = board_no

    def ensure_runtime_dirs(self) -> None:
        self.secrets.mkdir(parents=True, exist_ok=True)
        self.screenshots.mkdir(parents=True, exist_ok=True)
