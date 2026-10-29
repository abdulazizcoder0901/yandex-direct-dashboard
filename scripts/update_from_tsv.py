#!/usr/bin/env python3
"""data.json'ni Yandex Direct ulanishidan (MCP) olingan qisqa hisobotlar bilan yangilaydi.

Yandex API ilovasi tasdiqlanmaguncha GitHub Actions ma'lumot ola olmaydi; shu vaqtda Claude'ning
soatlik vazifasi oxirgi kunlar hisobotlarini TSV qilib saqlaydi va shu skript bilan birlashtiradi.

  python3 scripts/update_from_tsv.py --dir DIR --from 2026-10-28 --balance 345638.03 --available 245638.04 \\
      --base eski/data.json --out yangi/data.json

DIR ichida sarlavhasiz TSV fayllar: stats.tsv, placements.tsv, audience.tsv, regions.tsv, audience_place.tsv,
region_place.tsv (ustunlar tartibi fetch_data.REPORTS dagidek; oxirgi ikkitasi Clicks > 0 filtri bilan; yo'q fayl o'tkaziladi). --from dan boshlab eski qatorlar yangisi bilan almashtiriladi.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_data as f  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--from", dest="cut", required=True)
    ap.add_argument("--balance", type=float)
    ap.add_argument("--available", type=float)
    ap.add_argument("--base", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    d = json.loads(Path(a.base).read_text(encoding="utf-8"))
    for name, fields in f.REPORTS.items():
        src = Path(a.dir) / f"{name}.tsv"
        if not src.exists():  # bu hisobot berilmagan: eskisi qoladi
            print(f"{name}: fayl yo'q, o'zgarmadi")
            continue
        new = f.parse_tsv(src.read_text(encoding="utf-8"), fields)
        if any(r["Date"] < a.cut for r in new):
            sys.exit(f"{name}: --from ({a.cut}) dan oldingi qator bor")
        d[name] = [r for r in d.get(name, []) if r["Date"] < a.cut] + new
        tot = {m: round(sum(r[m] or 0 for r in new), 2) for m in f.METRICS}
        print(f"{name}: {len(new)} yangi qator, jami {tot}")
    if a.balance is not None:
        d["balance"] = [{"login": d.get("login"), "amount": a.balance,
                         "available": a.available if a.available is not None else a.balance, "currency": d.get("currency")}]
    # Qo'lda kiritiladigan kampaniya ma'lumotlari (holat, byudjet tarixi) har safar repodagi fayldan olinadi
    mc = f.ROOT / "data" / "manual_campaigns.json"
    if mc.exists():
        d["manual_campaigns"] = json.loads(mc.read_text(encoding="utf-8"))
    d["updated"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    d["today"] = datetime.datetime.now(f.TASHKENT).date().isoformat()
    Path(a.out).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    print("Yozildi:", a.out, d["updated"])


if __name__ == "__main__":
    main()
