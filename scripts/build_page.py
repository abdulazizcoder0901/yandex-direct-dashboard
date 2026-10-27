#!/usr/bin/env python3
"""site/index.html ni yig'adi: src/shell.html ichiga src/dashboard.html qo'yiladi.

src/dashboard.html Claude ichidagi dashboard sahifasining aynan o'zi. Uni o'zgartirgandan
keyin shu skriptni ishga tushiring: python3 scripts/build_page.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
shell = (ROOT / "src" / "shell.html").read_text(encoding="utf-8")
body = (ROOT / "src" / "dashboard.html").read_text(encoding="utf-8")
(ROOT / "site" / "index.html").write_text(shell.replace("<!-- DASHBOARD -->", body), encoding="utf-8")
thumbs = ROOT / "data" / "thumbs"
if thumbs.exists():
    shutil.copytree(thumbs, ROOT / "site" / "thumbs", dirs_exist_ok=True)
print("site/index.html yig'ildi")
