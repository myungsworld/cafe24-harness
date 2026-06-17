"""cf claude install — Claude Code 자산(슬래시 명령어·에이전트)을 ~/.claude 로 복사.

cafe24-harness 는 pipx venv 안에 산다 → 심링크는 재설치 때 깨진다. 그래서 **복사**한다(멱등).
`cf init` 이 자동 호출하고, `cf upgrade` 가 끝나며 조용히 재실행해 전파한다.

또한 seed_memory() 로 포터블 메모리 시드(작업습관 feedback + 몰별 persona 플레이스홀더)를
프로젝트 admin/memory/ 로 머지한다(멱등) — init 에서 호출.
"""
from __future__ import annotations

import re
from importlib import resources
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
CMD_DIR = CLAUDE_DIR / "commands" / "cafe24"
AGENT_DIR = CLAUDE_DIR / "agents"


def _pkg(*parts: str):
    base = resources.files("cafe24_harness")
    for p in parts:
        base = base / p
    return base


def _copy_if_changed(src_text: str, dest: Path, results: list) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.read_text(encoding="utf-8") == src_text:
        results.append((dest, "already"))
        return
    existed = dest.exists()
    dest.write_text(src_text, encoding="utf-8")
    results.append((dest, "updated" if existed else "installed"))


def _iter_md(pkg_dir) -> list:
    try:
        return sorted([p for p in pkg_dir.iterdir() if p.name.endswith(".md")], key=lambda p: p.name)
    except Exception:
        return []


def install(args=None) -> int:
    quiet = bool(getattr(args, "quiet", False))
    results: list = []

    # 1) 슬래시 명령어 → ~/.claude/commands/cafe24/
    for src in _iter_md(_pkg("claude", "commands", "cafe24")):
        _copy_if_changed(src.read_text(encoding="utf-8"), CMD_DIR / src.name, results)

    # 2) 에이전트 → ~/.claude/agents/  (cafe24-*.md 만)
    for src in _iter_md(_pkg("claude", "agents")):
        if not src.name.startswith("cafe24-"):
            continue
        _copy_if_changed(src.read_text(encoding="utf-8"), AGENT_DIR / src.name, results)

    if not quiet:
        changed = [r for r in results if r[1] != "already"]
        print(f"📦 Claude Code 자산 ({len(results)}개)")
        for dest, status in results:
            icon = "·" if status == "already" else "＋"
            print(f"  {icon} {str(dest).replace(str(Path.home()), '~')}  {status}")
        if not changed:
            print("  (모두 최신)")
    return 0


# ─── 메모리 시드 (init 에서 호출) ──────────────────────────────

_LINK_RE = re.compile(r"\]\(([^)]+\.md)\)")


def claude_project_memory_dir(project_root) -> Path:
    """Claude Code 가 세션 시작 때 자동 로드하는 그 프로젝트의 메모리 디렉토리.
    경로 키 = 프로젝트 절대경로의 '/' 와 '.' 를 '-' 로 치환 (Claude Code 인코딩).
    예: /Users/me/soomgo/healic → ~/.claude/projects/-Users-me-soomgo-healic/memory"""
    enc = re.sub(r"[/.]", "-", str(Path(project_root).resolve()))
    return Path.home() / ".claude" / "projects" / enc / "memory"


def seed_project_memory(project_root, quiet: bool = False) -> Path:
    """프로젝트의 자동 로드 메모리 디렉토리로 시드(멱등, 기존 파일·MEMORY.md 보존)."""
    mem = claude_project_memory_dir(project_root)
    out: list = []
    seed_memory(mem, out)
    if not quiet:
        print(f"🧠 프로젝트 메모리 시드 → {str(mem).replace(str(Path.home()), '~')}")
        for dest, status in out:
            icon = "·" if status.startswith("skip") else "＋"
            print(f"  {icon} {dest.name}  {status}")
    return mem


def seed_memory(memory_dir: Path, results: list | None = None) -> None:
    """패키지 claude/memory/*.md 를 프로젝트 memory_dir 로 머지(멱등).
    이미 있는 파일은 건드리지 않는다(작업하며 채운 페르소나 보존). MEMORY.md 는 줄 단위 머지."""
    out = results if results is not None else []
    memory_dir.mkdir(parents=True, exist_ok=True)
    seed_index = ""
    for src in _iter_md(_pkg("claude", "memory")):
        if src.name == "MEMORY.md":
            seed_index = src.read_text(encoding="utf-8")
            continue
        dest = memory_dir / src.name
        if dest.exists():
            out.append((dest, "skip(exists)"))
        else:
            dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            out.append((dest, "seeded"))
    _merge_index(memory_dir / "MEMORY.md", seed_index, out)


def _merge_index(dest: Path, seed_index: str, out: list) -> None:
    seed_lines = [ln for ln in seed_index.splitlines() if ln.strip().startswith("- [")]
    if not dest.exists():
        dest.write_text(seed_index, encoding="utf-8")
        out.append((dest, "seeded"))
        return
    existing = dest.read_text(encoding="utf-8")
    have = set(_LINK_RE.findall(existing))
    add = [ln for ln in seed_lines if not (set(_LINK_RE.findall(ln)) & have)]
    if not add:
        out.append((dest, "skip(all present)"))
        return
    sep = "" if existing.endswith("\n") else "\n"
    dest.write_text(existing + sep + "\n".join(add) + "\n", encoding="utf-8")
    out.append((dest, f"appended {len(add)} line(s)"))


def run(args) -> int:
    action = getattr(args, "claude_action", None)
    if action in (None, "install", "refresh"):
        return install(args)
    print("usage: cf claude install")
    return 1
