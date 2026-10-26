# ثابت کردن درستیِ prober

قانون پروژه: به هیچ ابزاری — از جمله ابزار خودمان — اعتماد نمی‌کنیم مگر اینکه هم «بله»ی درست و هم «نه»ی درست را ثابت کرده باشد.

## منابع حقیقت (خوانده شده، نه حدس)
- core.telegram.org/mtproto/mtproto-transports — obfuscation، padded intermediate
- tdlib `td/mtproto/TcpTransport.cpp` — ساخت header، قاب‌بندی رکورد TLS (`\x14\x03\x03\x00\x01\x01` + `\x17\x03\x03`)
- tdlib `td/mtproto/TlsInit.cpp` — padding هلو تا 517 بایت، چک HMAC پاسخ
- tdlib `td/mtproto/ProxySecret.cpp/.h`، `tdutils/.../base64.cpp`، `misc.cpp`، `HttpUrl.cpp`، `telegram/LinkManager.cpp`
- alexbers/mtprotoproxy @bd5b03c — سمت سرور (پین و vendor شده در `tests/refserver`)

## لایهٔ ۱: سرور مرجع محلی (در CI روی هر تغییر)
| مورد | انتظار | نتیجه |
|---|---|---|
| secret درست × (classic, dd, ee) | `dc` | ✅ |
| secret غلط × ۳ حالت | نه `dc` | ✅ |
| DC 1..5 | `dc` | ✅ |
| یک بیت تغییر در secret | نه `dc` | ✅ |
| سرور MASK (غریبه‌ها را به google می‌فرستد) + secret غلط | `tls:*` | ✅ |
| پورت بسته | `tcp:*` | ✅ |
| google.com / 1.1.1.1 / github.com با secret تصادفی | نه `dc` | ✅ |

**کنترل تست‌ها (sabotage):** چک nonce و ctor را عمداً غیرفعال کردم → **۸ تست از ۱۷ شکست خوردند**. یعنی تست‌ها واقعاً حساس‌اند. کد بعد از آن به نسخهٔ سالم برگردانده شد (sha256 چک شد).

## لایهٔ ۲: اوراکل TDLib (خودِ کلاینت تلگرام)
`tdjson` (TDLib 1.8.69 روی PyPI) متد `testProxy` را **قبل از لاگین** اجرا می‌کند. دو استفاده:

1. **پارس secret:** `testProxy` به `127.0.0.1:1` — اگر secret بد باشد، خطا شامل «secret» است. روی **۵۸۹ مورد** (۳۵۹ secret واقعی جمع‌آوری‌شده + ۲۳۰ مورد مرزی/تصادفی): **۰ اختلاف** (430 قبول، 159 رد).
   کنترل: `MAX_DOMAIN_LENGTH` را عمداً ۹۹۹ کردم → اوراکل **۶ اختلاف** پیدا کرد («Too long secret»). پس هارنس کور نیست. این تست در CI هم اجرا می‌شود (`tests/test_secret.py`).
2. **تست end-to-end:** نمونهٔ ۱۲۰ سرور تأییدشده (یکی از هر IP) + ۶۰ ردشده:
   - تأییدشدهٔ ما ← TDLib ok: **112/120**
   - ردشدهٔ ما ← TDLib fail: **52/60**
   - هر ۱۶ مورد اختلاف را **۳ بار با هر دو ابزار** دوباره تست کردم: همه نوسانی (flaky) بودند — مثلاً TDLib `['ok','Connection closed','ok','ok']` و ما `['dc','dc','dc','dc']`. **هیچ اختلاف سیستماتیکی نماند.**
   - روی ۴۰ موردی که ما `tls:bad-hello` دادیم، TDLib هم رد کرد (30 «Response hash mismatch»، 8 «First part of response to hello is invalid»، 2 timeout/closed).

## یک نکتهٔ مهم که اول اشتباه فهمیدم
اولین مقایسهٔ موازی با TDLib (۶۰ درخواست هم‌زمان) ۱۳۵۴ «اختلاف» داد: همه `Timeout expired` / `Handshake DH params timeout`. علت: TDLib در `testProxy` بعد از resPQ، **DH کامل** انجام می‌دهد که CPU‌بر است و در اجرای هم‌زمان timeout می‌شود. با اجرای ترتیبی/۸تایی، اختلاف‌ها به نوسان شبکه کاهش یافت. **ایراد از روش تست من بود، نه از پروژه.**

## پایداری تست‌های integration
۱ شکست در ۶ اجرا (`eof@tcp` روی DC تصادفی). بررسی:
- اتصال مستقیم ما به ۵ DC (بدون پروکسی) ۳۰۰/۳۰۰ موفق.
- سرور مرجع به‌تنهایی ۶۰۰/۶۰۰ موفق — وقتی با IPv4 به تلگرام وصل می‌شد.
- سرور مرجع پیش‌فرض `PREFER_IPV6=True` دارد؛ در conftest به `False` تغییر داده شد → **۶/۶ اجرا ۱۷/۱۷**. مشکل از محیط (IPv6 میزبان) بود، نه prober.
