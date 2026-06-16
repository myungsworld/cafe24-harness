"""프로젝트 설정 로드 + 경로/URL 해석.

프로젝트(admin 디렉토리)에는 config.yaml(mall_domain/shop_id/board_no)과
selectors/ 만 둔다. URL은 urls.py 템플릿으로 계산한다.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from . import urls

CONFIG_NAME = "config.yaml"
PLACEHOLDER_MALL = "__MALL__"  # cf init 시 --mall 미지정이면 이 값 → doctor가 경고


def resolve_admin_dir(explicit: str | None) -> Path:
    """admin 디렉토리 결정.
    --dir 우선 → ./admin/config.yaml → ./config.yaml(cwd 자체가 admin) 순.
    못 찾으면 기본 ./admin 반환(init 용)."""
    if explicit:
        return Path(explicit).resolve()
    cwd = Path.cwd()
    if (cwd / "admin" / CONFIG_NAME).exists():
        return (cwd / "admin").resolve()
    if (cwd / CONFIG_NAME).exists():
        return cwd.resolve()
    return (cwd / "admin").resolve()


class ProjectConfig:
    def __init__(self, admin_dir: Path):
        self.dir = Path(admin_dir).resolve()
        self.config_path = self.dir / CONFIG_NAME
        self.mall_domain = PLACEHOLDER_MALL
        self.shop_id = urls.SHOP_DEFAULT
        self.board_no = 4
        self.secrets = self.dir / "secrets"
        self.screenshots = self.dir / "screenshots"
        self.selectors_dir = self.dir / "selectors"
        self.state_file = self.secrets / "cafe24_state.json"

    @classmethod
    def load(cls, admin_dir: Path) -> "ProjectConfig":
        cfg = cls(admin_dir)
        if not cfg.config_path.exists():
            raise FileNotFoundError(
                f"설정이 없습니다: {cfg.config_path}\n  먼저 `cf init --mall <도메인>` 을 실행하세요."
            )
        data = yaml.safe_load(cfg.config_path.read_text(encoding="utf-8")) or {}
        cfg.mall_domain = data.get("mall_domain", PLACEHOLDER_MALL)
        cfg.shop_id = data.get("shop_id", urls.SHOP_DEFAULT)
        cfg.board_no = data.get("board_no", 4)
        return cfg

    # --- 파생 ---
    def is_configured(self) -> bool:
        return bool(self.mall_domain) and self.mall_domain != PLACEHOLDER_MALL

    def login_url(self) -> str:
        return urls.login_url(self.mall_domain, self.shop_id)

    def dashboard_url(self) -> str:
        return urls.dashboard_url(self.mall_domain, self.shop_id)

    def board_list_url(self) -> str:
        return urls.board_list_url(self.mall_domain, self.shop_id, self.board_no)

    def board_setting_url(self) -> str:
        return urls.board_setting_url(self.mall_domain, self.shop_id, self.board_no)

    def load_selectors(self, name: str = "cafe24_board") -> dict:
        p = self.selectors_dir / f"{name}.yaml"
        if not p.exists():
            return {}
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}

    def ensure_runtime_dirs(self) -> None:
        self.secrets.mkdir(parents=True, exist_ok=True)
        self.screenshots.mkdir(parents=True, exist_ok=True)

    def has_session(self) -> bool:
        return self.state_file.exists()
