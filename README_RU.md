<div align="center">

# Прокси для Телеграм бесплатно — проверенный список MTProto прокси

**Каждый прокси здесь передал настоящий запрос в настоящий дата-центр Telegram — трижды — прежде чем попасть в список.**

[![update](https://github.com/0xRadikal/Free-Telegram-Proxy/actions/workflows/update.yml/badge.svg)](https://github.com/0xRadikal/Free-Telegram-Proxy/actions/workflows/update.yml)
[![verified links](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2F0xRadikal%2FFree-Telegram-Proxy%2Fmain%2Findex.json&query=%24.funnel.verified_links&label=verified%20links&color=2ea44f)](verified/tg.txt)
[![servers](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2F0xRadikal%2FFree-Telegram-Proxy%2Fmain%2Findex.json&query=%24.funnel.verified_servers&label=real%20servers&color=0088cc)](resilient/tg.txt)
[![stars](https://img.shields.io/github/stars/0xRadikal/Free-Telegram-Proxy?style=flat)](https://github.com/0xRadikal/Free-Telegram-Proxy)

[English](README.md) · [فارسی](README_FA.md) · [Живая панель](https://0xradikal.github.io/Free-Telegram-Proxy/) · [Обсуждения](https://github.com/0xRadikal/Free-Telegram-Proxy/discussions)

</div>

Бесплатный открытый **список прокси для Телеграм**: рабочие **MTProto / MTProxy** прокси (FakeTLS `ee`, secure `dd` и обычные), список пересобирается примерно каждые 15 минут на GitHub Actions. Нажмите на ссылку — Telegram подключится сам, без приложений и регистрации. Для тех, у кого Telegram заблокирован или работает медленно. Работает в Telegram на Android, iPhone и Desktop. Проект не связан с Telegram.

## Начните отсюда — одна ссылка

100 прокси, которые не отказывают все разом: **один прокси на реальный сервер**, **не больше 5 на одну сеть** (ASN), отсортированы по **доказанной стабильности** в прошлых проверках, затем по скорости.

```
https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/top100.txt
```

Если `raw.githubusercontent.com` заблокирован, тот же путь через jsDelivr (кеш очищается после каждого обновления):

```
https://cdn.jsdelivr.net/gh/0xRadikal/Free-Telegram-Proxy@main/top100.txt
```

## Как подключить прокси в Телеграм

### Android и iPhone

1. Откройте [`top100.txt`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/top100.txt) (или [`resilient/tme.txt`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/resilient/tme.txt)) на телефоне.
2. Нажмите на любую строку. Telegram откроется и спросит **Подключить прокси?** — нажмите **Подключить**.
3. Не подключается? Попробуйте следующую строку: блокировки закрывают одни прокси и не трогают другие.

Вручную: **Настройки → Данные и память → Прокси → Добавить прокси → MTProto**, затем введите сервер, порт и секрет.

### Telegram Desktop (Windows, macOS, Linux)

Нажмите на ссылку `tg://proxy` или `https://t.me/proxy`, или откройте **Настройки → Продвинутые настройки → Тип соединения → Использовать собственный прокси → Добавить прокси → MTProto**.

### Выбор по типу или стране сервера

* **Только FakeTLS (`ee`)** — похож на обычный HTTPS, его обычно сложнее заблокировать: [`faketls/tme.txt`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/faketls/tme.txt)
* **Самые быстрые с точки проверки**: [`fast/tme.txt`](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/fast/tme.txt)
* **По стране сервера** — например, [Германия](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/DE.txt), [Нидерланды](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/NL.txt), [Россия](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/RU.txt). Это страна, где стоит сервер, **а не** страна, откуда он гарантированно работает; полный список — в [`countries/`](countries).

## Статистика в реальном времени

<!-- LIVE:BEGIN -->
**Последнее обновление:** `2026-10-28T14:22:49Z` · проверено из `US` (`LAX`)

| Этап | Количество |
|---|---:|
| ссылок собрано из всех источников | 3,417 |
| уникальных серверов (IP:порт) проверено | 1,889 |
| **прошли проверку во всех 3 раундах** (ссылки) | **1,948** |
| то же, в **реальных серверах** | **414** (371 IP) |
| доля самого частого IP среди проверенных ссылок | 1,054 (54.1%) |
| доля крупнейшей сети (`79.182.27.0/24`) среди проверенных ссылок | 1,054 (54.1%) |

`resilient` 371 · `fast` 97 · `stable` 344 · `verified` 1948 · `faketls` 109 · `secure` 92 · `classic` 180 · `all` 3417

[🇩🇪 DE 116](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/DE.txt) [🇮🇷 IR 98](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/IR.txt) [🇫🇮 FI 61](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FI.txt) [🇳🇱 NL 33](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/NL.txt) [🇷🇺 RU 16](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/RU.txt) [🇺🇸 US 12](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/US.txt) [🇫🇷 FR 7](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/FR.txt) [🇬🇧 GB 4](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/GB.txt) [🇵🇱 PL 4](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/PL.txt) [🇨🇭 CH 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/CH.txt) [🇸🇪 SE 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SE.txt) [🇸🇬 SG 3](https://raw.githubusercontent.com/0xRadikal/Free-Telegram-Proxy/main/countries/SG.txt)
<!-- LIVE:END -->

## Чем этот список отличается

| | обычный список | этот репозиторий |
|---|---|---|
| **Что значит «работает»** | порт открыт или «рукопожатие» | прокси передал `req_pq_multi` в дата-центр Telegram и получил ответ с **нашим случайным nonce** |
| **Сколько раз** | один | **в каждом раунде** (по умолчанию 3) — нестабильные прокси исключаются |
| **Что считается** | ссылки | ссылки **и реальные серверы** (`IP:порт` после DNS) |
| **Один оператор под сотней имён** | сотни повторов | `resilient/` — **одна ссылка на IP** |
| **Разбор secret** | regex | порт парсера TDLib, **сверенный с настоящей библиотекой TDLib** |

Если у домена несколько IPv4-адресов, Telegram подключается к тому, который DNS вернёт первым, поэтому здесь **каждый** IPv4-адрес домена должен пройти каждый раунд.

## Честные ограничения

* **Проверка из одного места.** «Проверен» значит *работает с сервера проверки* (его расположение — в `index.json`). Это **не** гарантирует, что прокси откроется у любого провайдера.
* Оператор прокси видит ваш IP-адрес и время подключения. Сообщения остаются зашифрованы собственным шифрованием Telegram (MTProto) — прокси не может их прочитать. Некоторые прокси могут показывать спонсорский канал в списке чатов.

## Частые вопросы

**Это бесплатные прокси для Телеграм?**  
Да. Это публичные MTProto прокси из открытых списков и Telegram-каналов; проект только проверяет и публикует их. Не нужны ни аккаунт, ни приложение. Код открыт (MIT).

**Как часто обновляется список?**  
Примерно каждые 15 минут. Время последнего обновления — в блоке статистики выше и в `index.json`.

**Чем отличаются MTProto, secure (dd) и FakeTLS (ee)?**  
Все это MTProto прокси. Секреты `dd` добавляют случайное заполнение к трафику; `ee` (FakeTLS) маскируют соединение под TLS к выбранному сайту, такой трафик сложнее распознать. Для каждого типа есть свой файл.

**Можно использовать список в своём боте или приложении?**  
Да. `index.json` перечисляет все файлы; в `proxies.json` для каждого прокси есть сервер, порт, секрет, тип, страна, ASN, задержка и аптайм. Сохраните уведомление MIT и указание DB-IP (CC BY 4.0).

Геоданные IP и ASN — [DB-IP](https://db-ip.com) (CC BY 4.0).

## Лицензия

MIT. Для образовательных и исследовательских целей; соблюдайте законы своей страны.
