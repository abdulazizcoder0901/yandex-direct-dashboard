# Yandex Direct dashboard

Junior IT akademiya reklama hisobi uchun dashboard, to'q fonda, tablarga bo'lingan (Umumiy, Telegram kanallari, Kampaniyalar, Auditoriya, Sayt va Metrika).

Davr filtrlari: Bugun, Kecha, 7 kun, 14 kun, 30 kun, Shu oy, O'tgan oy, oy tanlovi va ixtiyoriy sana oralig'i. Har bir ko'rsatkich oldingi xuddi shuncha kun bilan solishtiriladi; "← O'tgan oyda shu sana" tugmasi o'tgan oydagi aynan shu sanalar bilan solishtiradi.

- Konversiyalar, CPA, xarajat, kliklar, CPC va balans.
- Kunlik xarajat va konversiyalar grafiklari.
- Telegram kanallari: har bir kanal bo'yicha natija, konversiyasiz kanallarga ketgan pul, eng arzon konversiya bergan kanal.
- Kampaniyalar jadvali.
- Auditoriya: yosh, jins va hudud.
- Metrika: saytga tashriflar va "Forma yuborildi" maqsadi.

- `scripts/fetch_data.py` Yandex Direct API'dan butun tarix bo'yicha kunlik statistikani (kampaniya, kanal, yosh va jins, hudud), balansni va Metrika ma'lumotini olib, `site/data.json` faylini yozadi. Faqat Python standart kutubxonasi kerak.
- `src/dashboard.html` Claude ichidagi dashboard sahifasining aynan o'zi; `src/shell.html` uni oddiy sayt sifatida ishlatadi (ma'lumotni `data.json`'dan oladi va sana bo'yicha ajratadi).
- `scripts/build_page.py` ikkalasini `site/index.html` ga yig'adi. `src/` dagi fayllarni o'zgartirsangiz, uni qayta ishga tushiring.
- `.github/workflows/update.yml` har 10 daqiqada Yandex'dan ma'lumot olib, uni `data` branchiga `data.json` qilib yozadi (branchda doim bitta commit, tarix o'smaydi).
- Sayt **Netlify**'da: `site/` papkasi, build yo'q (`netlify.toml`). Sahifa ma'lumotni `data` branchidan o'qiydi va ochiq turganda har 10 daqiqada qayta o'qiydi. Shuning uchun Netlify faqat kod o'zgarganda deploy qiladi, ma'lumot yangilanganda emas.
- `data/manual_ads.json`, `data/manual_campaigns.json`, `data/thumbs/`: Yandex API bermaydigan narsalar (kreativ sarlavhalari, rasmlari, kampaniya holati), kabinet skrinshotlaridan.

**Repo public bo'lishi kerak:** sahifa `data.json` ni `raw.githubusercontent.com` dan o'qiydi, private repoda bu ishlamaydi. Public repoda GitHub Actions ham bepul (har 10 daqiqada ishlash oyiga ~4 300 daqiqa).

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

## 3. GitHub va Netlify'ni sozlash

1. Repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `YANDEX_DIRECT_TOKEN`: tokeningiz;
   - `YANDEX_DIRECT_LOGIN`: `junioritakademiya`.
2. **Actions → Ma'lumotni yangilash → Run workflow** bilan birinchi marta qo'lda ishga tushiring. Tugagach, repoda `data` branchi paydo bo'ladi.
3. Netlify'da: **Add new site → Import an existing project → GitHub** → `yandex-direct-dashboard` reposini tanlang. Sozlamalar `netlify.toml` dan o'zi olinadi (Publish directory: `site`). **Deploy** ni bosing.

4. Har 15 daqiqalik yangilash va "↻ Yangilash" tugmasi uchun (GitHub o'z jadvalini soatlab kechiktiradi,
   shuning uchun jadvalni Netlify yuritadi):
   - GitHub'da fine-grained token yarating: **Settings → Developer settings → Fine-grained tokens → Generate new token**;
     Repository access: **Only select repositories → yandex-direct-dashboard**; Permissions → **Actions: Read and write**.
   - Netlify'da: **Project configuration → Environment variables → Add a variable**: `GH_ACTIONS_TOKEN` = shu token.
   - **Deploys → Trigger deploy** bilan qayta deploy qiling (o'zgaruvchi funksiyalarga shundan keyin yetib boradi).

   Shundan keyin `netlify/functions/scheduled-refresh.mjs` har 15 daqiqada, `netlify/functions/refresh.mjs`
   esa tugma bosilganda GitHub'dagi "Ma'lumotni yangilash"ni ishga tushiradi.

**Muhim:** Netlify sayti internetda ochiq bo'ladi: manzilni bilgan har kim statistikani ko'ra oladi. Parol bilan yopish Netlify'ning pullik rejalarida bor.

## Hisoblash qoidalari

- Rasxod QQS'siz, hisob valyutasida (UZS), tiyingacha: Direct kabinetidagi "Расход" bilan bir xil.
- Konversiyalar Direct hisoblagan, kampaniyada tanlangan maqsadlar bo'yicha, Direct'ning standart atribusiya modelida (API maqsad ko'rsatilmasa boshqa modelni qabul qilmaydi).
- CPA = rasxod ÷ konversiyalar, CTR = kliklar ÷ ko'rsatishlar, CPC = rasxod ÷ kliklar, lid foizi = konversiyalar ÷ kliklar.
- ROI = (konversiyalar × 420 000 so'm − rasxod) ÷ rasxod. 420 000 so'm Metrika'dagi "Forma yuborildi" maqsadining qiymati; Direct o'zi daromad yozmaydi.
- Kampaniyalar tabida kampaniyani bossangiz, guruhlari (ads set), guruhni bossangiz, kreativlari ochiladi. Kreativlar "Kreativ N" deb yoziladi; to'liq sarlavha sichqoncha ustida (`data/manual_ads.json` dan).
- Yoqilgan va o'chgan sana: butun muddatdagi birinchi va oxirgi ko'rsatish kuni.
- Sanalar Toshkent vaqti bo'yicha. "7 kun", "14 kun", "30 kun" bugungi kunni ham o'z ichiga oladi. Solishtirish davri tanlangan davrdan oldingi xuddi shuncha kun.
- Konversiyasiz kanal: tanlangan davrda pul sarflangan, lekin birorta konversiya bo'lmagan kanal.
- Telegram reklamasi ko'pchilik ko'rsatishlar uchun yosh va jinsni bermaydi, Direct barcha ko'rsatishlarni "kompyuter" deb yozadi.
- Balans eski Live v4 API orqali olinadi (v5 API'da balans yo'q). Balans yoki Metrika olinmasa ham statistika baribir yangilanadi.
- Metrika hisoblagichi va maqsadini `METRIKA_COUNTER_ID` va `METRIKA_FORM_GOAL_ID` o'zgaruvchilari bilan almashtirish mumkin.
