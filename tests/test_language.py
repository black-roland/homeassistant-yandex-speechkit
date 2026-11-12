"""Language mapping and constant lists for Yandex SpeechKit."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _install_homeassistant_stub() -> None:
    """Stub homeassistant so package __init__ can load without the real core."""
    ha = types.ModuleType("homeassistant")
    ha.__path__ = []  # type: ignore[attr-defined]
    sys.modules["homeassistant"] = ha

    config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:  # noqa: D106
        pass

    config_entries.ConfigEntry = ConfigEntry
    sys.modules["homeassistant.config_entries"] = config_entries

    ha_const = types.ModuleType("homeassistant.const")

    class Platform:  # noqa: D106
        STT = "stt"
        TTS = "tts"

    ha_const.Platform = Platform
    sys.modules["homeassistant.const"] = ha_const

    ha_core = types.ModuleType("homeassistant.core")

    class HomeAssistant:  # noqa: D106
        pass

    ha_core.HomeAssistant = HomeAssistant
    sys.modules["homeassistant.core"] = ha_core


_install_homeassistant_stub()

from custom_components.yandex_speechkit.const import (  # noqa: E402
    DEFAULT_LANG,
    STT_LANGUAGES,
    TTS_LANGUAGES,
    TTS_VOICES,
    speechkit_language,
)

EXPECTED_STT_LANGUAGES = [
    "auto",
    "de-DE",
    "en-US",
    "es-ES",
    "fi-FI",
    "fr-FR",
    "he-HE",
    "it-IT",
    "kk-KZ",
    "nl-NL",
    "pl-PL",
    "pt-PT",
    "pt-BR",
    "ru",
    "sv-SE",
    "tr-TR",
    "uz-UZ",
]

EXPECTED_TTS_LANGUAGES = [
    "de-DE",
    "en-US",
    "he-IL",
    "kk-KK",
    "ru",
    "uz-UZ",
]

EXPECTED_RU_VOICES = [
    "alena",
    "filipp",
    "ermil",
    "jane",
    "madi_ru",
    "saule_ru",
    "omazh",
    "zahar",
    "dasha",
    "julia",
    "lera",
    "masha",
    "marina",
    "alexander",
    "kirill",
    "anton",
]


def test_speechkit_language_ac01() -> None:
    """AC-01: map ru to ru-RU; pass through all other codes."""
    assert speechkit_language("ru") == "ru-RU"
    assert speechkit_language("ru-RU") == "ru-RU"
    for code in ("en-US", "he-IL", "he-HE", "auto", "de-DE"):
        assert speechkit_language(code) == code


def test_default_lang() -> None:
    """DEFAULT_LANG is ru for Home Assistant."""
    assert DEFAULT_LANG == "ru"


def test_stt_languages() -> None:
    """STT list exposes ru, not ru-RU; he-HE unchanged."""
    assert STT_LANGUAGES == EXPECTED_STT_LANGUAGES
    assert "ru" in STT_LANGUAGES
    assert "ru-RU" not in STT_LANGUAGES
    assert STT_LANGUAGES.index("he-HE") == EXPECTED_STT_LANGUAGES.index("he-HE")


def test_tts_languages() -> None:
    """TTS outward list uses ru instead of ru-RU; he-IL present."""
    assert TTS_LANGUAGES == EXPECTED_TTS_LANGUAGES
    assert "ru" in TTS_LANGUAGES
    assert "ru-RU" not in TTS_LANGUAGES


def test_tts_voices_keys_and_ru_ru_voices() -> None:
    """Voices live under ru-RU only; list matches SpeechKit catalog."""
    assert "ru-RU" in TTS_VOICES
    assert "ru" not in TTS_VOICES
    assert "he-IL" in TTS_VOICES
    assert TTS_VOICES["ru-RU"] == EXPECTED_RU_VOICES


def test_ru_voices_via_mapping() -> None:
    """ru and ru-RU both resolve to the ru-RU voice bucket."""
    ru_voices = TTS_VOICES["ru-RU"]
    for lang in ("ru", "ru-RU"):
        assert TTS_VOICES[speechkit_language(lang)] == ru_voices
