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
- [ ] فعال کردن GitHub Pages (Settings → Pages → Source: GitHub Actions)
- [ ] تنظیم branch protection: اجازهٔ force-push فقط برای `github-actions` (مثل ریپوی v2ray)
- [ ] description و topics ریپو: `telegram` `mtproto` `mtproxy` `proxy` `free-proxy` `censorship` `iran`
- [ ] توکن ربات برای پست خودکار در @Raydikalx

## فاز بعد
- [ ] تحقیق RIPE Atlas از IR/RU (هزینه، مجاز بودن، دقت) — بدون ادعا تا اثبات
- [ ] README روسی و چینی
- [ ] QR کد top50
- [ ] auto-disable منبعی که N اجرا متوالی ۰ سرور انحصاری دارد (داده در state.json جمع می‌شود)
- [ ] پشتیبانی از SOCKS5 تلگرام (`tg://socks`) — نیاز به تحقیق جدا برای تست واقعی
