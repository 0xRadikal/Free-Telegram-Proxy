<div dir="rtl">

# پروکسی رایگان تلگرام

**هر پروکسی این‌جا قبل از انتشار، یک درخواست واقعی را به دیتاسنتر واقعی تلگرام رسانده — سه بار.**

[English](README.md) · [داشبورد زنده](https://0xradikal.github.io/Free-Telegram-Proxy/) · [کانال @Raydikalx](https://t.me/Raydikalx)

## از این‌جا شروع کن

کمترین تعداد لینک، بیشترین مقاومت: **از هر سرور واقعی فقط یک پروکسی**، مرتب‌شده بر اساس سرعت.

</div>

```
https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/top50.txt
```

<div dir="rtl">

روی گوشی کافی است روی یکی از خط‌ها بزنی؛ تلگرام باز می‌شود و می‌پرسد «اتصال به پروکسی؟».

## آمار زنده

</div>

<!-- LIVE:BEGIN -->
**آخرین به‌روزرسانی:** `2026-10-26T17:41:48Z` · محل تست: `US` (`ORD`)

| مرحله | تعداد |
|---|---:|
| لینک جمع‌آوری‌شده از همهٔ منابع | 3,251 |
| سرور یکتا (IP:پورت) که تست شد | 1,487 |
| **تأییدشده در همهٔ 3 دور** (لینک) | **1,688** |
| همان‌ها، بر حسب **سرور واقعی** | **388** (360 IP) |
| سهم بزرگ‌ترین اپراتور از لینک‌های تأییدشده | 454 (26.9%) |

`resilient` 360 · `fast` 1 · `stable` 0 · `verified` 1688 · `faketls` 119 · `secure` 86 · `classic` 163 · `all` 3251

[🇩🇪 DE 108](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/DE.txt) [🇮🇷 IR 99](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/IR.txt) [🇫🇮 FI 59](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FI.txt) [🇳🇱 NL 30](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/NL.txt) [🇷🇺 RU 13](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/RU.txt) [🇺🇸 US 11](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/US.txt) [🇵🇱 PL 9](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/PL.txt) [🇫🇷 FR 7](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FR.txt) [🇸🇪 SE 5](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SE.txt) [🇨🇭 CH 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/CH.txt) [🇸🇬 SG 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SG.txt) [🇬🇧 GB 2](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/GB.txt)
<!-- LIVE:END -->

<div dir="rtl">

## چه فرقی با بقیه دارد؟

| | لیست‌های معمول | این ریپو |
|---|---|---|
| **معنی «کار می‌کند»** | پورت باز است یا «handshake» | پروکسی درخواست `req_pq_multi` را به دیتاسنتر تلگرام رسانده و جواب با **nonce تصادفی ما** برگشته |
| **چند بار** | یک بار | **در همهٔ دورها** (پیش‌فرض ۳) |
| **چه چیزی شمرده می‌شود** | لینک | لینک **و سرور واقعی** (IP:پورت بعد از DNS) |
| **یک اپراتور با صدها اسم** | صدها بار تکرار | `resilient/` از هر IP فقط **یک لینک** |
| **پارس secret** | regex | پورت خط‌به‌خطِ پارسر TDLib که با **خودِ باینری TDLib** مقایسه و تست شده |
| **تاریخچه** | ندارد | درصد سالم‌بودن در ~۹۶ تست اخیر (`stable/`) |

### کشفی که این پروژه را شکل داد

در ۲۰۲۶-۱۰-۲۶ هفت لیست معروف را ادغام کردیم و همهٔ دامنه‌ها را resolve کردیم: **۹۵۸ لینک از ۱۳۹۴ لینک سالم فقط به یک IP می‌رسیدند.** اگر همان یک سرور بیفتد یا فیلتر شود، بیشتر آن لیست‌ها هم‌زمان از کار می‌افتند. به همین دلیل پیش‌فرض ما `resilient/` است.

## دسته‌ها

| دسته | معیار |
|---|---|
| **`resilient/`** | تأییدشده · **از هر IP یک لینک** — *پیشنهادی* |
| `fast/` | تأییدشده · زمان رفت‌وبرگشت از طریق پروکسی ≤ ۱۰۰ میلی‌ثانیه *از محل تست* |
| `stable/` | تأییدشده · حداقل ۹۰٪ تست‌های اخیر را پاس کرده (بعد از ~۳ ساعت تاریخچه ظاهر می‌شود) |
| `verified/` | در **همهٔ** دورها تست کامل را پاس کرده |
| `faketls/` · `secure/` · `classic/` | بر اساس نوع secret (`ee` · `dd` · ۱۶ بایتی) |
| `countries/XX.txt` | بر اساس کشور سرور |
| `all/` | همه، حتی مرده‌ها — برای پژوهش |

هر پوشه شامل `tg.txt`، `tme.txt` و `proxies.json` است (`all/` فقط `tg.txt`). `verified/` همهٔ لینک‌های سالم را دارد؛ بقیهٔ دسته‌ها از هر IP فقط یک لینک. دسته‌ای که در یک دور خالی باشد **حذف** می‌شود و هرگز خالی منتشر نمی‌شود.

اگر `raw.githubusercontent.com` فیلتر بود، ابتدای آدرس را با `https://cdn.jsdelivr.net/gh/0xRadikal/Free-Telegram-Proxy@main` عوض کن.

## محدودیت‌ها (صادقانه)

* **فقط از یک نقطه تست می‌شود.** «تأییدشده» یعنی از سرور تست کار کرده (محلش در `index.json`)؛ یعنی **تضمین نمی‌کند** از همراه اول یا ایرانسل باز شود.
* نمی‌توانیم ببینیم پروکسی کانال اسپانسری نشان می‌دهد یا نه.
* اپراتور پروکسی IP تو را می‌بیند؛ پیام‌ها با رمزنگاری خود تلگرام محافظت می‌شوند و پروکسی نمی‌تواند آن‌ها را بخواند.

موقعیت IP و ASN از [DB-IP](https://db-ip.com) (CC BY 4.0).

</div>
