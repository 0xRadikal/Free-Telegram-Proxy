<div dir="rtl">

# پروکسی رایگان تلگرام

**هر پروکسی این‌جا قبل از انتشار، یک درخواست واقعی را به دیتاسنتر واقعی تلگرام رسانده — سه بار.**

<p dir="ltr">

[![update](https://github.com/0xRadikal/Free-Telegram-Proxy/actions/workflows/update.yml/badge.svg)](https://github.com/0xRadikal/Free-Telegram-Proxy/actions/workflows/update.yml)
[![verified links](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2F0xRadikal%2FFree-Telegram-Proxy%2Fmain%2Findex.json&query=%24.funnel.verified_links&label=verified%20links&color=2ea44f)](verified/tg.txt)
[![servers](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2F0xRadikal%2FFree-Telegram-Proxy%2Fmain%2Findex.json&query=%24.funnel.verified_servers&label=real%20servers&color=0088cc)](resilient/tg.txt)
[![collected](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2F0xRadikal%2FFree-Telegram-Proxy%2Fmain%2Findex.json&query=%24.funnel.links_collected&label=links%20collected&color=lightgrey)](health.json)
[![stars](https://img.shields.io/github/stars/0xRadikal/Free-Telegram-Proxy?style=flat)](https://github.com/0xRadikal/Free-Telegram-Proxy)

</p>

[English](README.md) · [داشبورد زنده](https://0xradikal.github.io/Free-Telegram-Proxy/) · [کانال @Raydikalx](https://t.me/Raydikalx)

## از این‌جا شروع کن

۱۰۰ لینک که با هم از کار نمی‌افتند: **از هر سرور واقعی فقط یک پروکسی**، **از هر شبکه (ASN) حداکثر ۵ تا**، مرتب‌شده بر اساس **پایداری اثبات‌شده** در بررسی‌های قبلی و بعد سرعت.

</div>

```
https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/top100.txt
```

<div dir="rtl">

روی گوشی کافی است روی یکی از خط‌ها بزنی؛ تلگرام باز می‌شود و می‌پرسد «اتصال به پروکسی؟».

سقف ۵ از هر شبکه فقط وقتی بالا می‌رود که لیست بدون آن پر نشود — شبکه‌ها کم باشند، یا یک پروکسی اثبات‌شده جایش را به یک تازه‌وارد بی‌سابقه بدهد. سقفی که واقعاً استفاده شده در `index.json` با کلید `top100_info.network_cap` منتشر می‌شود. اگر قبلاً `top50.txt` را اضافه کرده‌ای، هنوز کار می‌کند: همان ۵۰ خط اول `top100.txt` است.

## آمار زنده

</div>

<!-- LIVE:BEGIN -->
**آخرین به‌روزرسانی:** `2026-10-27T07:46:31Z` · محل تست: `US` (`ORD`)

| مرحله | تعداد |
|---|---:|
| لینک جمع‌آوری‌شده از همهٔ منابع | 3,222 |
| سرور یکتا (IP:پورت) که تست شد | 1,849 |
| **تأییدشده در همهٔ 3 دور** (لینک) | **1,753** |
| همان‌ها، بر حسب **سرور واقعی** | **390** (356 IP) |
| سهم پرتکرارترین IP از لینک‌های تأییدشده | 967 (55.2%) |
| سهم بزرگ‌ترین شبکه (`79.182.27.0/24`) از لینک‌های تأییدشده | 967 (55.2%) |

`resilient` 356 · `fast` 94 · `stable` 326 · `verified` 1753 · `faketls` 118 · `secure` 89 · `classic` 158 · `all` 3222

[🇩🇪 DE 107](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/DE.txt) [🇮🇷 IR 96](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/IR.txt) [🇫🇮 FI 58](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FI.txt) [🇳🇱 NL 30](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/NL.txt) [🇷🇺 RU 16](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/RU.txt) [🇺🇸 US 13](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/US.txt) [🇫🇷 FR 7](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FR.txt) [🇵🇱 PL 7](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/PL.txt) [🇸🇪 SE 4](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SE.txt) [🇨🇭 CH 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/CH.txt) [🇸🇬 SG 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SG.txt) [🇬🇧 GB 2](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/GB.txt)
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

اگر یک دامنه به چند IP اشاره کند، تلگرام به هر کدام که DNS اول برگرداند وصل می‌شود؛ پس این‌جا **همهٔ IPv4های آن دامنه** باید در هر دور پاس شوند. در ۲۰۲۶-۱۰-۲۶، ۱۴ دامنه کنار یک IP سالم یک IP خراب داشتند.

### کشفی که این پروژه را شکل داد

در ۲۰۲۶-۱۰-۲۶ هفت لیست معروف را ادغام کردیم و همهٔ دامنه‌ها را resolve کردیم: **۹۵۸ لینک از ۱۳۹۴ لینک سالم فقط به یک IP می‌رسیدند.** اگر همان یک سرور بیفتد یا فیلتر شود، بیشتر آن لیست‌ها هم‌زمان از کار می‌افتند. به همین دلیل پیش‌فرض ما `resilient/` است.

## دسته‌ها

| دسته | معیار |
|---|---|
| **`top100.txt`** | ۱۰۰ لینک از `resilient` · اول پروکسی‌های اثبات‌شده (معیار `stable`) · مرتب بر اساس پایداری اثبات‌شده و بعد RTT · **از هر شبکه حداکثر ۵**، فقط در صورت نیاز بیشتر — *پیشنهادی*؛ `top50.txt` = ۵۰ خط اولش |
| **`resilient/`** | تأییدشده · **از هر IP یک لینک** (لینکی که طولانی‌ترین سابقهٔ بررسی را دارد نگه داشته می‌شود تا لینک ذخیره‌شدهٔ تو بین اجراها عوض نشود) — همهٔ سرورهای واقعی |
| `fast/` | سریع‌ترین ۲۵٪ از `resilient` بر اساس زمان رفت‌وبرگشت *از محل تست* |
| `stable/` | تأییدشده · حداقل ۹۰٪ تست‌های اخیر را پاس کرده (بعد از ~۳ ساعت تاریخچه ظاهر می‌شود) |
| `verified/` | در **همهٔ** دورها تست کامل را پاس کرده |
| `faketls/` · `secure/` · `classic/` | بر اساس نوع secret (`ee` · `dd` · ۱۶ بایتی) |
| `countries/XX.txt` | بر اساس کشور سرور |
| `all/` | همه، حتی مرده‌ها — برای پژوهش |

هر پوشه شامل `tg.txt`، `tme.txt` و `proxies.json` است (`all/` فقط `tg.txt`). `verified/` همهٔ لینک‌های سالم را دارد؛ بقیهٔ دسته‌ها از هر IP فقط یک لینک. دسته‌ای که در یک دور خالی باشد **حذف** می‌شود و هرگز خالی منتشر نمی‌شود.

اگر `raw.githubusercontent.com` فیلتر بود، همان مسیر را روی jsDelivr باز کن؛ مثلاً:

</div>

```
https://cdn.jsdelivr.net/gh/0xRadikal/Free-Telegram-Proxy@main/top100.txt
```

<div dir="rtl">

(بعد از هر اجرا کش jsDelivr پاک می‌شود.)

## محدودیت‌ها (صادقانه)

* **فقط از یک نقطه تست می‌شود.** «تأییدشده» یعنی از سرور تست کار کرده (محلش در `index.json`)؛ یعنی **تضمین نمی‌کند** از همراه اول یا ایرانسل باز شود.
* نمی‌توانیم ببینیم پروکسی کانال اسپانسری نشان می‌دهد یا نه.
* اپراتور پروکسی IP تو را می‌بیند؛ پیام‌ها با رمزنگاری خود تلگرام محافظت می‌شوند و پروکسی نمی‌تواند آن‌ها را بخواند.

موقعیت IP و ASN از [DB-IP](https://db-ip.com) (CC BY 4.0).

</div>
