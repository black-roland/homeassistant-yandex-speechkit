"""Constants for the Yandex SpeechKit integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

from yandex.cloud.ai.tts.v3.tts_pb2 import ContainerAudio

DOMAIN = "yandex_speechkit"
LOGGER = logging.getLogger(__package__)


# https://yandex.cloud/ru/docs/speechkit/stt/models
STT_LANGUAGES = [
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
    "ru-RU",
    "sv-SE",
    "tr-TR",
    "uz-UZ",
]

# https://yandex.cloud/ru/docs/speechkit/tts/voices
TTS_VOICES = {
    "de-DE": ["lea"],
    "en-US": ["john"],
    "he-IL": ["naomi"],
    "kk-KK": ["amira", "madi", "saule", "zhanar"],
    "ru-RU": [
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
    ],
    "uz-UZ": ["nigora", "lola", "yulduz"],
}

TTS_LANGUAGES = list(TTS_VOICES.keys())

TTS_OUTPUT_CONTAINERS = {
    "wav": ContainerAudio.WAV,
    "mp3": ContainerAudio.MP3,
    "ogg": ContainerAudio.OGG_OPUS,
}

PROXY_ERROR = "error"
PROXY_EMPTY_WAV = "empty_wav"
PROXY_EMPTY_MP3 = "empty_mp3"

CONF_TTS_UNSAFE = "tts_unsafe"
CONF_PROXY_SPEAKER = "proxy_speaker"
CONF_PROXY_MEDIA_TYPE = "proxy_media_type"

DEFAULT_LANG = "ru-RU"
DEFAULT_VOICE = "marina"
DEFAULT_OUTPUT_CONTAINER = "mp3"
