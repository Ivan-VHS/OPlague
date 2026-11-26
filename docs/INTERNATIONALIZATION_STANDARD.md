# Internationalization and language support

**Status:** i18n contract v1 and starter catalogs. This is the extensible locale foundation, not a claim that every screen or every human language is already translated.

## Universal policy

All well-formed BCP 47 tags are valid input. There is no finite language allowlist. A locale without a translated catalog remains usable for user text and platform formatting; untranslated product messages fall back through exact tag → script parent → language parent → English.

Baseline: UTF-8; Unicode 18.0; CLDR 49; BCP 47; grapheme-aware editing; font fallback; IME composition; bidi-safe mixed text; script-aware direction. Use host ICU/CLDR services rather than hand-written date, number, currency, calendar, plural or collation rules.

Machine contracts never change with UI language: hardware IDs, PCI/USB identifiers, hashes, CLI flags, JSON keys, diagnostic codes, package paths and serialized values remain invariant.

## OPlague adapter

The Python/Tk desktop adapter resolves stable message ids through trusted local catalogs. Persist the user's BCP 47 tag, derive direction and formatting from platform locale data, and use OS font fallback for scripts outside the default Latin/Cyrillic families. Tk controls, accessible names, menus, dialogs, tooltips and validation messages must share the same translator.

Inspection and security evidence remains read-only and locale-neutral. Never translate machine identifiers, hashes, driver metadata, file paths, JSON fields or command-line options. Never send typed text or inspected file contents to a translation service.

## Starter catalogs and CI

The v1 catalog set includes source English and reviewed Russian, Ukrainian, Simplified Chinese and Arabic common actions. `complete` means complete only against the starter message-id set, not against every UI string. New messages must use stable ids and pass human review before promotion.

Run `node tools/check_i18n.mjs`. GitHub Actions runs the same check on changes to i18n resources. Add GUI tests for RTL layout, Arabic/Hebrew shaping, CJK/Indic font fallback, IME composition, grapheme cursor/deletion, accessibility labels and locale switching.

## Adding a language

Add its canonical BCP 47 tag and local catalog, mark it `partial` until reviewed, verify placeholder parity and script direction, then mark `complete`. No cloud translation or remote locale dependency is permitted.
