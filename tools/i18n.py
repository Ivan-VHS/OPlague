"""Local BCP 47 message lookup for OPlague's desktop presentation layer."""
from __future__ import annotations

from dataclasses import dataclass
import locale as host_locale
import os
from pathlib import Path
import re
import json
from typing import Mapping

_LANGUAGE = re.compile(r"^[A-Za-z]{2,8}$")
_EXTLANG = re.compile(r"^[A-Za-z]{3}$")
_SCRIPT = re.compile(r"^[A-Za-z]{4}$")
_REGION = re.compile(r"^(?:[A-Za-z]{2}|[0-9]{3})$")
_VARIANT = re.compile(r"^(?:[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3})$")
_EXTENSION_SINGLETON = re.compile(r"^[0-9A-WY-Za-wy-z]$")
_SUBTAG = re.compile(r"^[A-Za-z0-9]{1,8}$")
_RTL_SCRIPTS = {"Arab", "Hebr", "Thaa", "Nkoo", "Adlm", "Rohg", "Syrc"}
_RTL_LANGUAGES = {"ar", "arc", "ckb", "dv", "fa", "he", "khw", "ks", "ps", "sd", "ug", "ur", "yi"}

# RFC 5646's grandfathered registry entries do not all follow the modern
# language-tag grammar. Keep their registered casing while accepting them.
_GRANDFATHERED_TAGS = {
    "art-lojban": "art-lojban",
    "cel-gaulish": "cel-gaulish",
    "en-gb-oed": "en-GB-oed",
    "i-ami": "i-ami",
    "i-bnn": "i-bnn",
    "i-default": "i-default",
    "i-enochian": "i-enochian",
    "i-hak": "i-hak",
    "i-klingon": "i-klingon",
    "i-lux": "i-lux",
    "i-mingo": "i-mingo",
    "i-navajo": "i-navajo",
    "i-pwn": "i-pwn",
    "i-tao": "i-tao",
    "i-tay": "i-tay",
    "i-tsu": "i-tsu",
    "no-bok": "no-bok",
    "no-nyn": "no-nyn",
    "sgn-be-fr": "sgn-BE-FR",
    "sgn-be-nl": "sgn-BE-NL",
    "sgn-ch-de": "sgn-CH-DE",
    "zh-guoyu": "zh-guoyu",
    "zh-hakka": "zh-hakka",
    "zh-min": "zh-min",
    "zh-min-nan": "zh-min-nan",
    "zh-xiang": "zh-xiang",
}


def _base_script(parts: list[str]) -> str:
    """Return only the script subtag in the base tag, never an extension value."""
    if not parts or parts[0].lower() == "x":
        return ""

    index = 1
    if len(parts[0]) <= 3:
        extlang_count = 0
        while index < len(parts) and extlang_count < 3 and _EXTLANG.fullmatch(parts[index]):
            index += 1
            extlang_count += 1

    if index < len(parts) and _SCRIPT.fullmatch(parts[index]):
        return parts[index].title()
    return ""


def canonical_locale_tag(value: str) -> str:
    """Validate and canonicalize a BCP 47 language tag."""
    if not isinstance(value, str):
        raise ValueError("locale tag must be a string")
    tag = value.strip().replace("_", "-")
    if not tag or len(tag) > 255:
        raise ValueError("locale tag is empty or too long")

    grandfathered = _GRANDFATHERED_TAGS.get(tag.casefold())
    if grandfathered is not None:
        return grandfathered

    parts = tag.split("-")
    if any(not part for part in parts):
        raise ValueError("locale tag contains an empty subtag")

    if parts[0].lower() == "x":
        if len(parts) < 2 or any(not _SUBTAG.fullmatch(item) for item in parts[1:]):
            raise ValueError("invalid BCP 47 private-use tag")
        return "-".join(["x", *(item.lower() for item in parts[1:])])

    if not _LANGUAGE.fullmatch(parts[0]):
        raise ValueError("invalid BCP 47 language subtag")

    output = [parts[0].lower()]
    index = 1
    if len(parts[0]) <= 3:
        extlangs = 0
        while index < len(parts) and extlangs < 3 and _EXTLANG.fullmatch(parts[index]):
            output.append(parts[index].lower())
            index += 1
            extlangs += 1
    if index < len(parts) and _SCRIPT.fullmatch(parts[index]):
        output.append(parts[index].title())
        index += 1
    if index < len(parts) and _REGION.fullmatch(parts[index]):
        region = parts[index]
        output.append(region.upper() if region.isalpha() else region)
        index += 1

    variants: set[str] = set()
    while index < len(parts) and _VARIANT.fullmatch(parts[index]):
        variant = parts[index].lower()
        if variant in variants:
            raise ValueError("duplicate BCP 47 variant")
        variants.add(variant)
        output.append(variant)
        index += 1

    extensions: set[str] = set()
    while index < len(parts) and _EXTENSION_SINGLETON.fullmatch(parts[index]):
        singleton = parts[index].lower()
        if singleton in extensions:
            raise ValueError("duplicate BCP 47 extension")
        extensions.add(singleton)
        output.append(singleton)
        index += 1
        start = index
        extension_subtags: list[str] = []
        while index < len(parts) and 2 <= len(parts[index]) <= 8 and _SUBTAG.fullmatch(parts[index]):
            extension_subtags.append(parts[index].lower())
            index += 1
        if index == start:
            raise ValueError("BCP 47 extension has no value")
        if singleton == "u":
            attributes: set[str] = set()
            keys: set[str] = set()
            active_key = False
            for subtag in extension_subtags:
                if len(subtag) == 2:
                    if subtag in keys:
                        raise ValueError("duplicate Unicode locale extension key")
                    keys.add(subtag)
                    active_key = True
                elif not active_key:
                    if subtag in attributes:
                        raise ValueError("duplicate Unicode locale extension attribute")
                    attributes.add(subtag)
        output.extend(extension_subtags)

    if index < len(parts) and parts[index].lower() == "x":
        output.append("x")
        index += 1
        start = index
        while index < len(parts) and _SUBTAG.fullmatch(parts[index]):
            output.append(parts[index].lower())
            index += 1
        if index == start:
            raise ValueError("BCP 47 private-use extension has no value")

    if index != len(parts):
        raise ValueError("invalid BCP 47 subtag sequence")
    return "-".join(output)


@dataclass(frozen=True, slots=True)
class LocaleContext:
    requested_tag: str
    resolved_tag: str
    direction: str
    messages: Mapping[str, str]
    source_messages: Mapping[str, str]

    @classmethod
    def load(cls, requested_tag: str | None = None, root: Path | None = None) -> "LocaleContext":
        base = root or Path(__file__).resolve().parents[1]
        manifest = json.loads((base / "i18n" / "manifest.v1.json").read_text(encoding="utf-8"))
        catalog_set = json.loads((base / "i18n" / "catalogs.v1.json").read_text(encoding="utf-8"))
        source_tag = manifest["sourceLocale"]
        source_messages = catalog_set["locales"][source_tag]["messages"]

        candidate = requested_tag
        if not candidate:
            candidate = os.environ.get("OPLAGUE_LOCALE")
        if not candidate:
            system_tag = host_locale.getlocale()[0] or "en"
            candidate = system_tag
        try:
            requested = canonical_locale_tag(candidate)
        except ValueError:
            requested = source_tag

        parts = requested.split("-")
        language = parts[0]
        requested_script = _base_script(parts)
        candidates = [requested]
        if requested_script:
            candidates.append(f"{language}-{requested_script}")
        candidates.append(language)
        candidates.append(source_tag)

        locales = catalog_set["locales"]
        resolved_tag = next((tag for tag in dict.fromkeys(candidates) if tag in locales), source_tag)
        pack = locales[resolved_tag]
        if requested_script:
            direction = "rtl" if requested_script in _RTL_SCRIPTS else "ltr"
        elif language.lower() in _RTL_LANGUAGES:
            direction = "rtl"
        else:
            direction = pack.get("direction", "ltr")
        if direction not in {"ltr", "rtl"}:
            direction = "ltr"

        return cls(
            requested_tag=requested,
            resolved_tag=resolved_tag,
            direction=direction,
            messages=pack["messages"],
            source_messages=source_messages,
        )

    def message(self, message_id: str, **values: object) -> str:
        template = self.messages.get(message_id) or self.source_messages.get(message_id) or message_id

        class SafeValues(dict):
            def __missing__(self, key: str) -> str:
                return "{" + key + "}"

        return template.format_map(SafeValues({key: str(value) for key, value in values.items()}))
