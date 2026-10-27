#!/usr/bin/env python3
"""Yandex Direct'dan statistika va balansni olib, site/data.json faylini yozadi.

Muhit o'zgaruvchilari:
  YANDEX_DIRECT_TOKEN  OAuth token (majburiy)
  YANDEX_DIRECT_LOGIN  Direct login, masalan junioritakademiya (ixtiyoriy)
  DAYS                 necha kunlik statistika olinadi (standart 365)

Faqat Python standart kutubxonasi ishlatiladi.
"""
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API_V5 = "https://api.direct.yandex.com/json/v5/"
API_V4_LIVE = "https://api.direct.yandex.ru/live/v4/json/"
FIELDS = ["Date", "CampaignId", "CampaignName", "Impressions", "Clicks", "Cost", "Conversions"]
NUMERIC = {"Impressions", "Clicks", "Cost", "Conversions"}
TASHKENT = datetime.timezone(datetime.timedelta(hours=5))
OUT = Path(__file__).resolve().parent.parent / "site" / "data.json"


def post(url, body, headers):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
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


def get_currency(token, login):
    status, _, text = post(API_V5 + "clients",
                           {"method": "get", "params": {"FieldNames": ["Login", "Currency"]}},
                           v5_headers(token, login))
    data = json.loads(text)
    if status != 200 or "error" in data:
        raise RuntimeError("clients.get xatosi: " + text[:500])
    client = data["result"]["Clients"][0]
    return client["Login"], client["Currency"]


def get_report(token, login, date_from, date_to):
    body = {"params": {
        "SelectionCriteria": {"DateFrom": date_from, "DateTo": date_to},
        "FieldNames": FIELDS,
        "ReportName": "dashboard-" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d%H%M%S"),
        "ReportType": "CUSTOM_REPORT",
        "DateRangeType": "CUSTOM_DATE",
        "Format": "TSV",
        "IncludeVAT": "YES",
        "AttributionModels": ["LC"],
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
        status, resp_headers, text = post(API_V5 + "reports", body, headers)
        if status == 200:
            return text
        if status in (201, 202) and time.time() < deadline:
            wait = int(resp_headers.get("retryIn") or resp_headers.get("Retryin") or 10)
            print(f"Hisobot tayyorlanmoqda, {wait} soniya kutamiz...")
            time.sleep(wait)
            continue
        raise RuntimeError(f"Reports xatosi ({status}): {text[:500]}")


def parse_tsv(text):
    rows = []
    for line in text.splitlines():
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) != len(FIELDS):
            raise RuntimeError("Kutilmagan qator: " + line[:200])
        rec = {}
        for name, value in zip(FIELDS, cells):
            if name in NUMERIC:
                rec[name] = None if value in ("", "--") else float(value)
            else:
                rec[name] = value
        rows.append({
            "date": rec["Date"],
            "campaign_id": rec["CampaignId"],
            "campaign": rec["CampaignName"],
            "impressions": rec["Impressions"],
            "clicks": rec["Clicks"],
            "cost": rec["Cost"],
            "conversions": rec["Conversions"],
        })
    return rows


def get_balance(token, login):
    """Balans faqat eski Live v4 API'da bor. Xato bo'lsa None qaytaradi."""
    param = {"Action": "Get", "SelectionCriteria": {"Logins": [login]}}
    status, _, text = post(API_V4_LIVE, {"method": "AccountManagement", "token": token, "locale": "ru", "param": param}, {})
    try:
        data = json.loads(text)
        if status != 200 or "error_code" in data:
            raise RuntimeError(text[:300])
        acc = data["data"]["Accounts"][0]
        return {"amount": float(acc["Amount"]), "available": float(acc["AmountAvailableForTransfer"]), "currency": acc["Currency"]}
    except Exception as e:  # balans ixtiyoriy: statistika baribir yoziladi
        print("Ogohlantirish: balans olinmadi:", e, file=sys.stderr)
        return None


def main():
    token = os.environ.get("YANDEX_DIRECT_TOKEN")
    if not token:
        sys.exit("YANDEX_DIRECT_TOKEN berilmagan.")
    login = os.environ.get("YANDEX_DIRECT_LOGIN") or None
    days = int(os.environ.get("DAYS", "365"))

    date_to = datetime.datetime.now(TASHKENT).date() - datetime.timedelta(days=1)
    date_from = date_to - datetime.timedelta(days=days - 1)

    login, currency = get_currency(token, login)
    rows = parse_tsv(get_report(token, login, date_from.isoformat(), date_to.isoformat()))
    balance = get_balance(token, login)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "login": login,
        "currency": currency,
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "balance": balance,
        "rows": rows,
    }, ensure_ascii=False), encoding="utf-8")
    print(f"{len(rows)} qator yozildi: {OUT}")


if __name__ == "__main__":
    main()
