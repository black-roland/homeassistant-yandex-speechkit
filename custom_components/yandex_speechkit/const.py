"""Constants for the Yandex SpeechKit integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import logging

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
