# Accessibility

The proxy list exists for people whose internet is restricted, often on old phones, slow connections, small screens, or with a screen reader or keyboard only. If you hit a barrier on the site or in the lists, please tell us: it is a bug, and you do not need to explain why you need the fix.

This page covers the website at https://0xradikal.github.io/Free-Telegram-Proxy/ (English and Persian), the plain-text lists, and the repository's own documents. It describes what has been tested and what has not. It is not a claim of WCAG conformance.

## Priorities

- **Everything works without a mouse.** Every link, button, filter and copy action can be reached and used with the keyboard, in a logical order, with a visible focus ring.
- **Persian is a first-class language.** The Persian pages are written right-to-left (`dir="rtl"`) with `lang="fa"`. Words in the other language, such as the language switch, are marked with their own `lang`.
- **The lists do not need the site.** `top100.txt`, `verified/tme.txt` and the other files are plain text, one link per line, readable by any screen reader, terminal or script. The home page says so in a `<noscript>` message when JavaScript is off.
- **Motion is optional.** Animations stop when the system asks for reduced motion, and a *Pause motion* button stops them for everyone.
- **Our aspirational target is WCAG 2.2 level AA.** We aim for it but have not claimed it, because no full manual evaluation has been done.

## What was evaluated

Evaluated on 2026-10-28 by the maintainer, on the six site pages (`/`, `/fa/`, `/methodology/`, `/fa/methodology/`, `/data/`, `/fa/data/`), with Chrome for Testing 151:

| Check | Tool / method | Result |
|---|---|---|
| Automated rules | Lighthouse 12.8.2 accessibility category (axe-core 4.14) | 100 on all six pages, no failing audits after this change. Before it, `/fa/` failed *label-content-name-mismatch* on the language switch. |
| Keyboard | Tab through each page in a scripted browser | Every visible interactive element was reached (65 on each home page, 20 on each guide page). The first stop is the *Skip to…* link. Every stop showed a focus indicator after this change; before it, the search field had none. |
| Reflow | 320 CSS px wide viewport | No horizontal scrolling on any page |
| Text spacing | WCAG 1.4.12 spacing applied with a user style | No text clipped or hidden |
| Motion | `prefers-reduced-motion: reduce`, and the *Pause motion* button pressed by keyboard | 0 running animations in both cases. The button's state is exposed with `aria-pressed`. |

The ten checks that Lighthouse lists as manual were not all verified. The site has **not** been tested with a screen reader (NVDA, JAWS, VoiceOver, TalkBack) or with real users with disabilities. Automated tools catch only part of the barriers people meet.

The static parts are guarded by tests in `tests/test_site.py`, which run on every pull request. They check language and direction attributes, that accessible names contain the visible text, that the search field keeps its focus ring, and that every animation stops under reduced motion.

## Contributor expectations

- **Any change to `docs/`:** run `python -m pytest -q tests/test_site.py`, and say in the pull request how you checked the change with the keyboard. If you change colours, give the contrast ratio (at least 4.5:1 for text, 3:1 for large text and focus indicators).
- **Fixed in this repository:** keep `lang`/`dir`, keep visible text inside the accessible name, never remove a focus outline without a replacement, and keep new animations to `transform`/`opacity` with a reduced-motion rule.
- **New text:** add it in both languages through the translation table in `docs/app.js` (`data-t` keys). The test `test_static_text_matches_translation_table` fails if a key is missing or the static text differs from the table.
- **Screenshots or recordings:** welcome, but describe the change in words as well.

## Reporting accessibility issues

Use the form **[Accessibility barrier](https://github.com/0xRadikal/Free-Telegram-Proxy/issues/new?template=accessibility.yml)**. It asks what you were trying to do, the page, and what happened. Browser, device and assistive technology are optional but help us reproduce the problem. You never have to say anything about a disability. Screenshots are optional.

If you cannot use the GitHub form, post in [Discussions → Q&A](https://github.com/0xRadikal/Free-Telegram-Proxy/discussions/categories/q-a), or write to the Telegram channel [@Raydikalx](https://t.me/Raydikalx). English and Persian are both fine.

### Severity

The maintainer sets the severity during triage; reporters do not need to.

- **Blocker:** you cannot get a working proxy link at all. Examples: the list cannot be reached by keyboard, or a control has no name for a screen reader.
- **Serious:** the task is possible but much harder. Examples: no visible focus, low contrast on key text, motion that cannot be stopped.
- **Minor:** it is annoying, but there is an easy way around it.

### How we respond

This is a single-maintainer, unpaid project, so there are no guaranteed timelines. Blockers come before any other site work. Issues get the `accessibility` label and a reply when they are triaged. If a fix will take time, we will point to a workaround; the plain-text lists are always one. You will be asked to confirm the fix if you are willing.

## Ownership and maintenance

The maintainer, [@0xRadikal](https://github.com/0xRadikal), owns accessibility for the site and the documents. Pull requests that touch `docs/` are reviewed against the expectations above. The evaluation table is re-run and its date updated after any redesign of the site, and at least once a year. If maintenance passes to someone else, this file passes with it.

## Supported environments

The site is plain HTML, CSS and a small script. It is designed for current versions of Chrome, Edge, Firefox and Safari, on desktop and mobile, at widths down to 320 px, with keyboard or touch. Testing so far has been with Chromium only (see the table above). Firefox, Safari and every screen reader are untested; please report anything that does not work there. The plain-text lists work anywhere text can be opened.

## Known limitations

- **No screen reader testing yet.** Names, roles and live announcements are set in the markup but have not been confirmed with a real screen reader.
- **Connecting is done by Telegram.** A *Connect* link hands off to the Telegram app, whose own accessibility this project does not control. To avoid it, copy the link, or add a proxy by hand: Settings → Data and Storage → Proxy.
- **The interactive filters need JavaScript.** Without it, the home page shows a link to the Top 100 text list instead.
- **Third-party documents.** Proxy data comes from third-party sources and is shown as plain text. Server names can be long, unreadable hostnames.

## Feedback and improvements

Suggestions about this statement or about how we test, such as tools, checklists or wording, are welcome in [Discussions → Ideas](https://github.com/0xRadikal/Free-Telegram-Proxy/discussions/categories/ideas) or as a pull request to this file. Please report an actual barrier with the form above, so it is tracked and labelled.
