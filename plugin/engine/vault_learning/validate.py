"""Validate Mermaid diagrams by rendering them with mermaid-cli (mmdc).

Optional: without mermaid-cli the engine still works and reports the diagrams
as unchecked. It looks for mmdc in $VL_MERMAID_DIR, then in engine/mermaid
(`npm install` there, with PUPPETEER_SKIP_DOWNLOAD=1 to reuse an installed
Chrome or Edge), then on PATH (`npm install -g @mermaid-js/mermaid-cli`).
All diagrams render in one browser launch; on failure each is rendered alone
to name the offender.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MMDC_DIRS = [Path(os.environ["VL_MERMAID_DIR"])] if os.environ.get("VL_MERMAID_DIR") else []
MMDC_DIRS.append(ROOT / "mermaid")
BROWSERS = [
    os.environ.get("CHROME_PATH", ""),
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


class ValidatorUnavailable(RuntimeError):
    pass


def _mmdc() -> Path:
    for d in MMDC_DIRS:
        for name in ("mmdc.cmd", "mmdc"):
            p = d / "node_modules" / ".bin" / name
            if p.exists():
                return p
    on_path = shutil.which("mmdc")
    if on_path:
        return Path(on_path)
    raise ValidatorUnavailable("mermaid-cli not installed (see SETUP.md, optional diagram checks)")


def _puppeteer_config(tmp: Path) -> Path | None:
    """A config pointing at an installed browser, or None to use puppeteer's own."""
    exe = next((b for b in BROWSERS if b and Path(b).is_file()), None)
    if not exe:
        return None
    cfg = tmp / "puppeteer.json"
    cfg.write_text(json.dumps({"executablePath": exe, "args": ["--no-sandbox"]}), encoding="utf-8")
    return cfg


def _run(mmdc: Path, cfg: Path | None, src: Path, out: Path) -> tuple[bool, str]:
    cmd = [str(mmdc), "-q"] + (["-p", str(cfg)] if cfg else []) + ["-i", str(src), "-o", str(out)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          timeout=600, shell=False)
    msg = (proc.stderr or proc.stdout or "").strip().splitlines()
    return proc.returncode == 0, "\n".join(msg[:4])


def validate(diagrams: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return [(label, error)] for diagrams that fail to render. Empty = all good."""
    if not diagrams:
        return []
    mmdc = _mmdc()
    tmp = Path(tempfile.mkdtemp(prefix="vault-learning-mmd-"))
    try:
        cfg = _puppeteer_config(tmp)
        md = tmp / "all.md"
        md.write_text("\n\n".join(f"```mermaid\n{code}\n```" for _, code in diagrams) + "\n",
                      encoding="utf-8")
        ok, _ = _run(mmdc, cfg, md, tmp / "all-out.md")
        if ok:
            svgs = list(tmp.glob("all-out-*.svg"))
            if len(svgs) == len(diagrams):
                return []
        failures = []
        for i, (label, code) in enumerate(diagrams):
            src = tmp / f"d{i}.mmd"
            src.write_text(code, encoding="utf-8")
            ok, err = _run(mmdc, cfg, src, tmp / f"d{i}.svg")
            if not ok:
                failures.append((label, err or "render failed"))
        return failures
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
