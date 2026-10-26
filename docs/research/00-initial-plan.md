# Free-Telegram-Proxy: تحقیق، شواهد و نقشهٔ ساخت

> تاریخ تحقیق: 2026-10-26 · محل تست: Frankfurt, DE (AS214902)
> همهٔ عددهای این فایل **اندازه‌گیری شده‌اند** و اسکریپت و داده‌ی خامشان در همین پوشه است
> (`probe.py` · `probe_results.json` · `stable.json` · `*.txt` = snapshot رقبا).

---

## 1. رقبا (اندازه‌گیری شده، نه از روی README)

| ریپو | ★ | آپدیت | اندازه‌ی لیست | پایدار در ۳ دور تست | توضیح |
|---|---|---|---|---|---|
| SoliSpirit/mtproto | 1928 | ۱۲ ساعت | 131 | 105 (**80.2%**) | فقط یک فایل txt، بدون JSON، بدون آمار |
| ALIILAPRO/MTProtoProxy | 157 | ۳۰ دقیقه | 131 | — | `mtproto.txt` آن **بایت‌به‌بایت با SoliSpirit یکسان است** (`cmp`) |
| Grim1313/mtproto-for-telegram | 169 | ۱۲ ساعت | — | — | کامیت‌ها: «sync proxies from SoliSpirit» (کپی) |
| tgmtproxy/telegram-mtproto-proxy-list | 209 | ۱ ساعت | 900 | 891 (99.0%) | **644 لینک** از 900 همان یک secret هستند |
| tgproxypink/telegram-proxy-list | 2 | ۱ ساعت | 500 | 492 (98.4%) | **389 لینک** همان secret بالا |
| Argh94/Proxy-List (MTProto.txt) | 242 | ۱ ساعت | 253 | 236 (93.3%) | |
| dubblebyte/free-mtproto-proxies | 19 | ۸ ساعت | 74 | 35 (**47.3%**) | ادعای «handshake-verified» دارد |

### کشف کلیدی: «تعداد پروکسی» در این حوزه باد کرده است
اجتماع همه‌ی لیست‌ها = **1476 لینک یکتا**. بعد از resolve کردن DNS:

- **1394 لینک پایدار → فقط 275 جفت `IP:port` واقعی و 253 IP یکتا.**
- **958 لینک (69%) روی یک IP واحد هستند:** `191.44.90.24` (AS201861، هلسینکی).
  با DoH گوگل و کلادفلر هم چک شد — artifact ابزار من نیست.

یعنی یک اپراتور با صدها ساب‌دامین، تقریباً کل «حجم» رقبای پرتعداد را ساخته. اگر آن سرور بیفتد/فیلتر شود، ۷۰٪ لیست آن‌ها هم‌زمان می‌میرد.
**این مهم‌ترین مزیت رقابتی ماست: شمردن و رتبه‌بندی بر اساس سرور واقعی، نه لینک.**

---

## 2. اثبات امکان فنی تست واقعی (end-to-end)

`probe.py` پروتکل را از روی سند رسمی تلگرام (mtproto-transports → Transport obfuscation)
و پیاده‌سازی سرور مرجع (`alexbers/mtprotoproxy`) و پارسر خود تلگرام (`tdlib ProxySecret.cpp`) نوشته شده.

سطح‌های اثبات:

| سطح | چه چیزی را ثابت می‌کند |
|---|---|
| `tcp` | پورت باز است (هر سروری می‌تواند) |
| `tls` | فقط برای `ee`: HMAC در ServerHello با **secret ما** درست است ← سرور secret را می‌داند |
| `dc` | پروکسی `req_pq_multi` را به **دیتاسنتر واقعی تلگرام** رساند و `resPQ` با **nonce تصادفی ما** برگشت ← بدون اتصال واقعی به تلگرام جعل‌شدنی نیست |

### صحت‌سنجی خود ابزار (قبل از اعتماد به نتایجش)
| تست | نتیجه |
|---|---|
| سرور مرجع محلی، secret درست، حالت plain / dd / ee | هر سه ← `dc` ✅ |
| همان سرور، secret غلط (هر سه حالت) | هیچ‌کدام `dc` نشد ✅ |
| سرور با MASK (ترافیک ناشناس به google فوروارد می‌شود) + secret غلط | رد شد (`tls:not-handshake`) ✅ |
| google.com / 1.1.1.1 / github.com / IP واقعی DC تلگرام با secret تصادفی | هیچ‌کدام `dc` نشد ✅ |
| ۱۵ پروکسی سالم با **یک بیت** تغییر در secret | 0/15 رد نشدند ← یعنی همه درست رد شدند ✅ |
| DC 1..5 و media DC (-2, -4) | همه کار می‌کنند؛ DC2 پیش‌فرض کافی است |
| سرعت | 1476 پروکسی در **۱۲ ثانیه** (concurrency=200) |

### باگی که پیدا شد — در ابزار خودم، نه در داده‌ها
اول 6 پروکسی با خطای `ascii decode` رد می‌شدند. بررسی `tdlib`:
`get_domain() { return secret_.substr(17); }` ← دامنه بایت خام است، نه ASCII.
بعد از اصلاح، همان‌ها `dc` شدند. (قانون پروژه: پارسر ما باید **دقیقاً** مثل tdlib رفتار کند.)

قواعد پارس secret مطابق tdlib: hex → base64url → base64؛ طول 16 / 17 با `dd` / ≥18 با `ee`؛ حداکثر 17+182 بایت.

---

## 3. محدودیت‌ها (صادقانه، باید در README هم بیاید)

1. **تست از آلمان/آمریکا ≠ کار کردن در ایران/روسیه.** `dc` یعنی «پروکسی سالم است و به تلگرام وصل می‌شود»، نه «از ایرانسل باز است».
   - مسیر بررسی‌نشده‌ی آینده: RIPE Atlas الان **102 probe متصل در IR** و 608 در RU دارد (API چک شد). امکان اندازه‌گیری TCP از داخل ایران با Atlas **هنوز تست نشده** — در فاز 6 باید راستی‌آزمایی شود، تا آن موقع هیچ ادعایی نمی‌کنیم.
2. نمی‌توانیم بفهمیم پروکسی کانال اسپانسری (ad tag) نشان می‌دهد یا نه — این بعد از auth است و در سطح resPQ دیده نمی‌شود.
3. اپراتور پروکسی IP کاربر را می‌بیند؛ پیام‌ها رمز شده‌اند. این باید در FAQ بیاید.

---

## 4. معماری پیشنهادی

```
sources (GitHub raw + t.me/s/<channel>)        ← 3 کانال تست شد: 41 / 50 / 20 لینک
   │  fetch async, retry, per-source health
   ▼
L0 parse (tdlib-exact)  → normalize → dedup key = (host, port, secret_bytes)
L1 DNS resolve (A/AAAA) → server identity = (IP, port)    ← ضد تورم
L2 TCP connect
L3 FakeTLS HMAC (ee)
L4 DC resPQ + nonce echo     × 3 دور با فاصله  → stable
   │
   ▼
rank: median RTT, stability history (state.json), server diversity cap
   │
   ▼
publish (rolling squash روی main، مثل Free-v2ray-Configs)
```

### خروجی‌ها (tiers)
| مسیر | معیار |
|---|---|
| `verified/` | در **هر ۳ دور** به سطح `dc` رسیده |
| `fast/` | verified و median RTT کمتر از آستانه |
| `diverse/` | verified + **حداکثر N لینک برای هر IP** ← لیستی که با افتادن یک سرور نمی‌میرد |
| `faketls/` · `secure/`(dd) · `classic/` | بر اساس نوع secret |
| `countries/XX` | بر اساس GeoIP سرور |
| `top50.txt` | بهترین‌ها |
| `all/` | همه (اکثراً تست‌نشده/مرده هم دارد) |

فرمت‌ها در هر tier: `tg://` · `https://t.me/proxy` · `proxies.json` (host/port/secret/type/domain/ip/country/rtt/first_seen/last_seen/stability) · `proxies.csv`.
فراداده: `index.json` (قرارداد، همه‌ی URLها) · `health.json` (سلامت منابع + گزارش funnel) · `state.json` (تاریخچه).

قوانین منتقل‌شده از ریپوی v2ray (تجربه‌ی اثبات‌شده): فایل خالی هرگز منتشر نشود · خروجی deterministic · rolling squash با `--force-with-lease` · fail-closed · cron */5 + freshness gate.

---

## 5. فازها و TODO

### فاز 0 — پایه
- [ ] اسکلت ریپو در `0xRadikal/Free-Telegram-Proxy` (الان **کاملاً خالی** است، 0 کامیت — چک شد)
- [ ] `pyproject`, pytest, ruff, LICENSE (MIT), SECURITY, CONTRIBUTING
- [ ] CI: تست + lint روی هر push

### فاز 1 — Collector
- [ ] رجیستری منابع (`sources.py`) با وزن/وضعیت
- [ ] پارسر tdlib-exact + تست‌های واحد (همه‌ی حالت‌های hex/base64/base64url/طول/نوع/دامنه‌ی بایتی/URL-encoded/`server=host.`)
- [ ] اسکرپر `t.me/s/` با رعایت rate limit
- [ ] dedup + resolve + شناسه‌ی سرور

### فاز 2 — Prober (هسته‌ی تمایز)
- [ ] تبدیل `probe.py` به ماژول تمیز + تست‌ها
- [ ] **تست یکپارچه در CI با سرور مرجع** (مثبت + منفی) — مثل همین تحقیق
- [ ] ۳ دور، median RTT، دلیل رد شدن هر مورد
- [ ] محدودیت هم‌زمانی برای هر IP (مودب بودن با سرورهای مشترک)

### فاز 3 — Publisher
- [ ] tierها، فرمت‌ها، index/health/state
- [ ] نام‌گذاری پایدار و محتوا-محور
- [ ] rolling squash + guardها

### فاز 4 — ظاهر
- [ ] README قوی (EN/FA/RU/ZH) با funnel واقعی، QR، جدول tierها
- [ ] داشبورد GitHub Pages (بدون tracker، fallback به jsDelivr)

### فاز 5 — زمان‌بندی و پایداری
- [ ] cron */5 + freshness gate + `repository_dispatch`
- [ ] auto-disable منابع کم‌بازده (مثل state.json ریپوی v2ray)

### فاز 6 — دید از داخل کشورهای فیلتر (تحقیقی، بدون ادعا تا اثبات)
- [ ] بررسی RIPE Atlas (هزینه‌ی credit، نوع measurement مجاز، دقت)
- [ ] امکان runner در منطقه‌ی دیگر

### فاز 7 — کانال و جامعه
- [ ] پست خودکار بهترین‌ها در @Raydikalx
- [ ] issue template برای گزارش پروکسی خراب

---

## 6. تصمیم‌هایی که باید صاحب پروژه بگیرد
1. اسم ریپو: `Free-Telegram-Proxy` (موجود، خالی) یا اسم دیگر؟
2. لینک‌های اپراتور غالب (`191.44.90.24`) را کامل حذف کنیم یا فقط در `diverse/` محدود کنیم؟ (پیشنهاد: در `verified` بمانند، در `diverse` و `top50` سقف داشته باشند.)
3. برند در خروجی: MTProxy لینک «remark» ندارد؛ برند فقط در README/JSON/کانال ممکن است.
