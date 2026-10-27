# Yandex Direct dashboard

Junior IT akademiya reklama hisobi uchun dashboard. 30 kun, 90 kun yoki 1 yil oralig'ini tanlash mumkin, har bir ko'rsatkich oldingi shuncha kun bilan solishtiriladi.

- Konversiyalar, CPA, xarajat, kliklar, CPC va balans.
- Kunlik xarajat va konversiyalar grafiklari.
- Telegram kanallari: har bir kanal bo'yicha natija, konversiyasiz kanallarga ketgan pul, eng arzon konversiya bergan kanal.
- Kampaniyalar jadvali.
- Auditoriya: yosh, jins va hudud.
- Metrika: saytga tashriflar va "Forma yuborildi" maqsadi.

- `scripts/fetch_data.py` Yandex Direct API'dan butun tarix bo'yicha kunlik statistikani (kampaniya, kanal, yosh va jins, hudud), balansni va Metrika ma'lumotini olib, `site/data.json` faylini yozadi. Faqat Python standart kutubxonasi kerak.
- `site/index.html` shu faylni o'qib, dashboardni chizadi. Sahifa Claude ichidagi dashboard bilan bir xil kodda yozilgan.
- `.github/workflows/update.yml` har kuni soat 08:00 da (Toshkent vaqti) ma'lumotni yangilaydi va saytni GitHub Pages'ga joylaydi.

`site/data.json` repoga yozilmaydi (`.gitignore`), ya'ni statistika Git tarixida saqlanmaydi.

## 1. Yandex OAuth token olish

1. Direct kabinetida **Инструменты → API** bo'limini oching va API'ga kirish ruxsatini oling (agar hali olinmagan bo'lsa).
2. https://oauth.yandex.ru/client/new sahifasida ilova yarating:
   - platforma: **Веб-сервисы**, Redirect URI: `https://oauth.yandex.ru/verification_code`;
   - ruxsatlar: **Яндекс.Директ → Использование API Яндекс.Директа** (`direct:api`) va **Яндекс.Метрика → Получение статистики** (`metrika:read`).
3. Ilovaning **ClientID** qiymatini oling va brauzerda oching:
   `https://oauth.yandex.ru/authorize?response_type=token&client_id=<ClientID>`
4. Direct hisobiga ega Yandex akkaunt bilan kiring. Sahifada chiqqan token sizning `YANDEX_DIRECT_TOKEN` qiymatingiz bo'ladi.

Token parol bilan teng: uni hech kimga yubormang va kodga yozmang.

## 2. Kompyuterda ishga tushirish

```bash
export YANDEX_DIRECT_TOKEN="tokeningiz"
export YANDEX_DIRECT_LOGIN="junioritakademiya"
python3 scripts/fetch_data.py
python3 -m http.server 8000 --directory site
```

So'ng brauzerda http://localhost:8000 ni oching.

## 3. GitHub'da har kuni avtomatik yangilash

1. Repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `YANDEX_DIRECT_TOKEN`: tokeningiz;
   - `YANDEX_DIRECT_LOGIN`: `junioritakademiya`.
2. Repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. **Actions → Dashboard yangilash → Run workflow** tugmasi bilan birinchi marta qo'lda ishga tushiring.

**Muhim:** GitHub Pages sayti repo private bo'lsa ham internetda ochiq bo'ladi. Saytni faqat GitHub Enterprise Cloud rejasida yopish mumkin. Manzilni bilgan har kim xarajat va kampaniya statistikasini ko'ra oladi. Agar bu mos kelmasa, Pages'ni yoqmang va dashboardni faqat kompyuterda oching (2-bo'lim).

## Hisoblash qoidalari

- Xarajat QQS bilan, hisob valyutasida (UZS).
- Konversiyalar Direct hisoblagan, kampaniyada tanlangan maqsadlar bo'yicha, oxirgi bosish (LC) atribusiya modelida.
- CPA = xarajat ÷ konversiyalar, CTR = kliklar ÷ ko'rsatishlar, CPC = xarajat ÷ kliklar.
- Davrlar kecha bilan tugaydi; oldingi davr undan oldingi xuddi shuncha kun.
- Konversiyasiz kanal: tanlangan davrda pul sarflangan, lekin birorta konversiya bo'lmagan kanal.
- Telegram reklamasi ko'pchilik ko'rsatishlar uchun yosh va jinsni bermaydi, Direct barcha ko'rsatishlarni "kompyuter" deb yozadi.
- Balans eski Live v4 API orqali olinadi (v5 API'da balans yo'q). Balans yoki Metrika olinmasa ham statistika baribir yangilanadi.
- Metrika hisoblagichi va maqsadini `METRIKA_COUNTER_ID` va `METRIKA_FORM_GOAL_ID` o'zgaruvchilari bilan almashtirish mumkin.
