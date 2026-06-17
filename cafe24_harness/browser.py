"""Playwright 컨텍스트/세션/페이지 덤프 (config 주입형).

프로젝트 경로(secrets/screenshots/state)는 ProjectConfig에서 가져온다.
"""
from __future__ import annotations

import json
import time

from .config import ProjectConfig


def new_context(p, cfg: ProjectConfig, headless: bool = True, use_state: bool = True):
    """chromium 컨텍스트 생성. 저장된 세션이 있으면 재사용.
    반환: (browser, context, page)"""
    browser = p.chromium.launch(headless=headless)
    kwargs = {"viewport": {"width": 1440, "height": 1000}, "locale": "ko-KR"}
    if use_state and cfg.state_file.exists():
        kwargs["storage_state"] = str(cfg.state_file)
    context = browser.new_context(**kwargs)
    return browser, context, context.new_page()


def shot(cfg: ProjectConfig, page, name: str):
    cfg.screenshots.mkdir(parents=True, exist_ok=True)
    path = cfg.screenshots / f"{int(time.time())}_{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


# --- 내부 ---

def _frame_text(frame) -> str:
    try:
        return frame.evaluate("() => document.body ? document.body.innerText : ''") or ""
    except Exception:
        return ""


def _dump_tables(frame) -> list:
    try:
        return frame.evaluate(
            """() => {
                const out = [];
                document.querySelectorAll('table').forEach((t, ti) => {
                    const rows = [];
                    t.querySelectorAll('tr').forEach(tr => {
                        const cells = Array.from(tr.querySelectorAll('th,td'))
                            .map(c => (c.innerText || '').replace(/\\s+/g, ' ').trim());
                        if (cells.some(x => x)) rows.push(cells);
                    });
                    if (rows.length) out.push({ index: ti, rows });
                });
                return out;
            }"""
        ) or []
    except Exception:
        return []


def dump_page(cfg: ProjectConfig, page, selectors: dict, label: str) -> dict:
    """현재 page(+모든 frame)를 스크린샷 + DOM 텍스트/테이블로 덤프.
    selectors: target_reviews / status_keywords / writer_keyword 키 사용."""
    targets = selectors.get("target_reviews", [])
    status_kw = selectors.get("status_keywords", [])
    writer_kw = selectors.get("writer_keyword", "")

    report = {
        "label": label,
        "url": page.url,
        "frames": [],
        "matched_rows": [],
        "status_found": [],
    }

    report["screenshot"] = str(shot(cfg, page, label))

    for fr in page.frames:
        txt = _frame_text(fr)
        info = {
            "url": fr.url,
            "text_len": len(txt),
            "has_status_kw": [k for k in status_kw if k in txt],
            "has_target": [t for t in targets if t in txt],
            "has_writer_kw": bool(writer_kw) and writer_kw in txt,
            "has_gojeong": ("글고정" in txt) or ("고정글" in txt),
        }
        report["frames"].append(info)

        if info["has_target"] or info["has_writer_kw"] or info["has_gojeong"] or "작성자" in txt:
            for tb in _dump_tables(fr):
                for row in tb["rows"]:
                    joined = " | ".join(row)
                    if any(t in joined for t in targets) or (writer_kw and writer_kw in joined):
                        report["matched_rows"].append(joined)
                    for k in status_kw:
                        if k in joined and k not in report["status_found"]:
                            report["status_found"].append(k)

    dump_path = cfg.screenshots / f"{int(time.time())}_{label}_dump.json"
    dump_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["dump_file"] = str(dump_path)
    return report


def dump_raw(cfg: ProjectConfig, page, label: str) -> dict:
    """제네릭 덤프 — 판단은 호출자(에이전트)가 한다.
    각 프레임의 본문 텍스트(발췌) + 테이블 + 링크 + 버튼을 그대로 뽑아 JSON 저장."""
    report = {"label": label, "url": page.url, "frames": []}
    report["screenshot"] = str(shot(cfg, page, label))
    for fr in page.frames:
        try:
            data = fr.evaluate(
                r"""() => {
                    const norm = s => (s||'').replace(/\s+/g,' ').trim();
                    const tables = [];
                    document.querySelectorAll('table').forEach(t => {
                        const rows = [];
                        t.querySelectorAll('tr').forEach(tr => {
                            const c = [...tr.querySelectorAll('th,td')].map(x => norm(x.innerText));
                            if (c.some(v => v)) rows.push(c);
                        });
                        if (rows.length) tables.push(rows);
                    });
                    const links = [...document.querySelectorAll('a')].map(a => ({
                        t: norm(a.innerText).slice(0,40),
                        href: (a.getAttribute('href')||'').slice(0,120),
                        onclick: (a.getAttribute('onclick')||'').slice(0,100),
                    })).filter(x => x.t || x.href);
                    const buttons = [...document.querySelectorAll('button, a.btnNormal, input[type=button]')].map(b => ({
                        id: b.id||'', t: norm(b.innerText || b.value).slice(0,30),
                        onclick: (b.getAttribute('onclick')||'').slice(0,100),
                    })).filter(x => x.t || x.id);
                    return { url: location.href, text: norm(document.body ? document.body.innerText : '').slice(0,2500),
                             tables, links: links.slice(0,250), buttons: buttons.slice(0,120) };
                }"""
            )
        except Exception:
            data = {"url": fr.url, "text": "", "tables": [], "links": [], "buttons": []}
        report["frames"].append(data)
    dump = cfg.screenshots / f"{int(time.time())}_{label}_raw.json"
    dump.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["dump_file"] = str(dump)
    return report


def print_raw_summary(report: dict) -> None:
    print("\n" + "=" * 60)
    print(f"열림 — {report['url']}")
    print(f"  스크린샷: {report.get('screenshot')}")
    print(f"  덤프(JSON): {report.get('dump_file')}")
    for i, fr in enumerate(report["frames"]):
        if fr.get("text") or fr.get("tables") or fr.get("links"):
            print(f"  · frame[{i}] {fr['url'][:70]} — 텍스트 {len(fr.get('text',''))}자 / 테이블 {len(fr.get('tables',[]))} / 링크 {len(fr.get('links',[]))} / 버튼 {len(fr.get('buttons',[]))}")
    print("  → 상세는 위 JSON 파일을 읽어 판단.")


def print_summary(report: dict) -> None:
    print("\n" + "=" * 60)
    print(f"요약 — {report.get('label')}")
    print("=" * 60)
    print(f"- URL: {report['url']}")
    print(f"- 스크린샷: {report.get('screenshot')}")
    print(f"- 덤프: {report.get('dump_file')}")
    print(f"- 발견된 상태 키워드: {report['status_found'] or '(없음)'}")
    print(f"- 타깃 후기 매칭 행: {len(report['matched_rows'])}개")
    for r in report["matched_rows"][:12]:
        print(f"    · {r[:120]}")
    busy = [f for f in report["frames"] if f["has_target"] or f["has_writer_kw"] or f["has_gojeong"]]
    print(f"- 게시판 내용 프레임: {len(busy)}개")
    for f in busy:
        print(f"    · {f['url'][:90]} (status_kw={f['has_status_kw']}, 글고정={f['has_gojeong']})")
