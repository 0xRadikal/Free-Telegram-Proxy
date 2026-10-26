# نقشهٔ راه

## انجام‌شده در این مرحله
- [x] پارسر secret و لینک = TDLib (تست تفاضلی با باینری TDLib)
- [x] prober end-to-end (TCP → FakeTLS HMAC → obfuscated2 → resPQ با nonce)
- [x] تست integration با سرور مرجع پین‌شده (مثبت + منفی + sabotage)
- [x] ۲۴ منبع اندازه‌گیری‌شده؛ ۳۹ کاندید ردشده با دلیل
- [x] DNS → شناسهٔ سرور؛ DB-IP کشور + ASN
- [x] tierها: resilient, fast, stable, verified, faketls, secure, classic, countries, all, top50
- [x] index.json / health.json / state.json
- [x] README زنده EN + FA، داشبورد GitHub Pages
- [x] workflow: CI، update (cron + gate + rolling squash + lease)، pages
- [x] شبیه‌سازی انتشار با race واقعی

## بعد از اولین انتشار (نیاز به تأیید/اقدام مالک)
- [x] فعال کردن GitHub Pages (workflow)
- [x] ruleset روی main (deletion + linear history) و tags
- [x] description و topics ریپو
- [ ] توکن ربات برای پست خودکار در @Raydikalx — **عمداً انجام نشد** (درخواست مالک)
- [ ] جایگزینی PAT کلاسیک با توکن fine-grained (فقط Contents/Actions روی همین ریپو)

## فاز بعد
- [ ] تحقیق RIPE Atlas از IR/RU (هزینه، مجاز بودن، دقت) — بدون ادعا تا اثبات
- [x] تست همهٔ IPهای یک دامنه (round-robin)
- [x] معیار `top_network_share` (ASN یا prefix)
- [ ] سقف تنوع شبکه در top50 — بعد از شبیه‌سازی روی چند روز دادهٔ state
- [ ] README روسی و چینی
- [ ] تاریخچهٔ per-IP (الان per-link است؛ alias جدید یک سرور قدیمی تاریخچه ندارد)
- [ ] پایش اجرای cron گیتهاب (تا الان همهٔ اجراها از trigger سرور بوده)
- [ ] `stable/` تا ~12 بررسی (~3 ساعت) خالی است — طبیعی، ولی در README توضیح داده شود
- [ ] QR کد top50
- [ ] auto-disable منبعی که N اجرا متوالی ۰ سرور انحصاری دارد (داده در state.json جمع می‌شود)
- [ ] پشتیبانی از SOCKS5 تلگرام (`tg://socks`) — نیاز به تحقیق جدا برای تست واقعی
