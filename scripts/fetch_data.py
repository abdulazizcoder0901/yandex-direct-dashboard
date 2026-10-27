#!/usr/bin/env python3
"""Yandex Direct va Metrika'dan ma'lumot olib, site/data.json faylini yozadi.

Muhit o'zgaruvchilari:
  YANDEX_DIRECT_TOKEN  OAuth token (majburiy; direct:api va metrika:read ruxsatlari bilan)
  YANDEX_DIRECT_LOGIN  Direct login, masalan junioritakademiya (ixtiyoriy)
  METRIKA_COUNTER_ID   Metrika hisoblagichi (standart 112358613, "Telegram ads")
  METRIKA_FORM_GOAL_ID "Forma yuborildi" maqsadi (standart 609995532)

Faqat Python standart kutubxonasi ishlatiladi.
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_V5 = "https://api.direct.yandex.com/json/v5/"
API_V4_LIVE = "https://api.direct.yandex.ru/live/v4/json/"
METRIKA_API = "https://api-metrika.yandex.net/stat/v1/data"
NUMERIC = {"Impressions", "Clicks", "Cost", "Conversions"}
METRICS = ["Impressions", "Clicks", "Cost", "Conversions"]
# Sahifadagi hisob-kitoblar shu ustun nomlarini kutadi (Direct'dagi nomlar bilan bir xil).
REPORTS = {
    "stats": ["Date", "CampaignId", "CampaignName", "AdGroupId", "AdGroupName", "AdId"] + METRICS,
    "placements": ["Date", "Placement"] + METRICS,
    "audience": ["Date", "Age", "Gender"] + METRICS,
    "regions": ["Date", "LocationOfPresenceName"] + METRICS,
}
TASHKENT = datetime.timezone(datetime.timedelta(hours=5))
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data.json"


def request(url, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    if data:
        req.add_header("Content-Type", "application/json; charset=utf-8")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


def v5_headers(token, login):
    h = {"Authorization": "Bearer " + token, "Accept-Language": "ru"}
    if login:
        h["Client-Login"] = login
    return h


def get_account(token, login):
    status, _, text = request(API_V5 + "clients",
                              {"method": "get", "params": {"FieldNames": ["Login", "Currency"]}},
                              v5_headers(token, login))
    data = json.loads(text)
    if status != 200 or "error" in data:
        raise RuntimeError("clients.get xatosi: " + text[:500])
    client = data["result"]["Clients"][0]
    return client["Login"], client["Currency"]


def get_report(token, login, name, fields):
    body = {"params": {
        "SelectionCriteria": {},
        "FieldNames": fields,
        "ReportName": f"dashboard-{name}-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S"),
        "ReportType": "CUSTOM_REPORT",
        "DateRangeType": "ALL_TIME",
        "Format": "TSV",
        "IncludeVAT": "NO",  # kabinetdagi "Расход" kabi, QQS'siz
    }}
    headers = v5_headers(token, login)
    headers.update({
        "processingMode": "auto",
        "returnMoneyInMicros": "false",
        "skipReportHeader": "true",
        "skipColumnHeader": "true",
        "skipReportSummary": "true",
    })
    deadline = time.time() + 600
    while True:
        status, resp_headers, text = request(API_V5 + "reports", body, headers)
        if status == 200:
            return parse_tsv(text, fields)
        if status in (201, 202) and time.time() < deadline:
            wait = int(resp_headers.get("retryIn") or resp_headers.get("Retryin") or 10)
            print(f"{name}: hisobot tayyorlanmoqda, {wait} soniya kutamiz...")
            time.sleep(wait)
            continue
        raise RuntimeError(f"{name}: Reports xatosi ({status}): {text[:500]}")


def parse_tsv(text, fields):
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) != len(fields):
            raise RuntimeError("Kutilmagan qator: " + line[:200])
        rec = {}
        for name, value in zip(fields, cells):
            if name in NUMERIC:
                rec[name] = None if value in ("", "--") else float(value)
            else:
                rec[name] = value
        rows.append(rec)
    return rows


def get_balance(token, login):
    """Balans faqat eski Live v4 API'da bor. Xato bo'lsa None qaytaradi."""
    param = {"Action": "Get", "SelectionCriteria": {"Logins": [login]}}
    status, _, text = request(API_V4_LIVE, {"method": "AccountManagement", "token": token, "locale": "ru", "param": param})
    try:
        data = json.loads(text)
        if status != 200 or "error_code" in data:
            raise RuntimeError(text[:300])
        return [{"login": a["Login"], "amount": float(a["Amount"]),
                 "available": float(a["AmountAvailableForTransfer"]), "currency": a["Currency"]}
                for a in data["data"]["Accounts"]]
    except Exception as e:  # balans ixtiyoriy: statistika baribir yoziladi
        print("Ogohlantirish: balans olinmadi:", e, file=sys.stderr)
        return None


def get_library(token, login):
    """Kutubxonadagi video kreativlar va rasmlar. Xato bo'lsa (None, None) qaytaradi."""
    try:
        status, _, text = request(API_V5 + "creatives", {"method": "get", "params": {
            "SelectionCriteria": {}, "FieldNames": ["Id", "Type", "Name"], "Page": {"Limit": 10000}}},
            v5_headers(token, login))
        data = json.loads(text)
        if status != 200 or "error" in data:
            raise RuntimeError(text[:300])
        videos = [{"Id": str(c["Id"]), "Type": c["Type"], "Name": c["Name"]} for c in data["result"].get("Creatives", [])]
        status, _, text = request(API_V5 + "adimages", {"method": "get", "params": {
            "SelectionCriteria": {}, "FieldNames": ["AdImageHash", "Name", "Associated", "Type"], "Page": {"Limit": 10000}}},
            v5_headers(token, login))
        data = json.loads(text)
        if status != 200 or "error" in data:
            raise RuntimeError(text[:300])
        images = [{"AdImageHash": i["AdImageHash"], "Name": i["Name"], "Associated": i["Associated"], "Type": i["Type"]}
                  for i in data["result"].get("AdImages", [])]
        return videos, images
    except Exception as e:
        print("Ogohlantirish: kreativlar kutubxonasi olinmadi:", e, file=sys.stderr)
        return None, None


def get_metrika(token, counter_id, goal_id):
    """Oxirgi bir yildagi kunlik tashriflar va forma maqsadi. Xato bo'lsa None qaytaradi."""
    query = urllib.parse.urlencode({
        "ids": counter_id,
        "metrics": f"ym:s:visits,ym:s:goal{goal_id}reaches",
        "dimensions": "ym:s:date",
        "date1": "365daysAgo",
        "date2": "today",
        "limit": 1000,
    })
    status, _, text = request(METRIKA_API + "?" + query, headers={"Authorization": "OAuth " + token})
    try:
        data = json.loads(text)
        if status != 200:
            raise RuntimeError(text[:300])
        return [{"date": row["dimensions"][0]["name"],
                 "visits": float(row["metrics"][0]), "form_submits": float(row["metrics"][1])}
                for row in data["data"]]
    except Exception as e:
        print("Ogohlantirish: Metrika ma'lumoti olinmadi:", e, file=sys.stderr)
        return None


def main():
    token = (os.environ.get("YANDEX_DIRECT_TOKEN") or "").strip()
    # Butun manzil nusxalangan bo'lsa (...#access_token=...&...), faqat tokenning o'zini olamiz
    if "access_token=" in token:
        token = token.split("access_token=", 1)[1].split("&", 1)[0]
    if not token:
        sys.exit("YANDEX_DIRECT_TOKEN berilmagan.")
    # Token qiymatini emas, faqat ko'rinishini chiqaramiz: noto'g'ri qiymat qo'yilganini bilish uchun
    print(f"Token: {len(token)} belgi, y0_ bilan boshlanadi: {token.startswith('y0_')}")
    login = (os.environ.get("YANDEX_DIRECT_LOGIN") or "").strip() or None
    counter_id = os.environ.get("METRIKA_COUNTER_ID", "112358613")
    goal_id = os.environ.get("METRIKA_FORM_GOAL_ID", "609995532")

    login, currency = get_account(token, login)
    out = {
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "today": datetime.datetime.now(TASHKENT).date().isoformat(),
        "login": login,
        "currency": currency,
    }
    for name, fields in REPORTS.items():
        out[name] = get_report(token, login, name, fields)
        print(f"{name}: {len(out[name])} qator")
    out["balance"] = get_balance(token, login)
    out["videos"], out["images"] = get_library(token, login)
    # API bermaydigan, kabinetdan qo'lda qo'shilgan e'lonlar (hech qachon ko'rsatilmaganlar)
    manual = ROOT / "data" / "manual_ads.json"
    out["manual_ads"] = json.loads(manual.read_text(encoding="utf-8")) if manual.exists() else []
    mc = ROOT / "data" / "manual_campaigns.json"
    out["manual_campaigns"] = json.loads(mc.read_text(encoding="utf-8")) if mc.exists() else []
    for r in out["manual_ads"]:
        r["Thumb"] = r.get("ThumbFile") if (ROOT / "site" / str(r.get("ThumbFile"))).exists() else None
    out["metrika"] = get_metrika(token, counter_id, goal_id)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"Yozildi: {OUT}")


if __name__ == "__main__":
    main()
