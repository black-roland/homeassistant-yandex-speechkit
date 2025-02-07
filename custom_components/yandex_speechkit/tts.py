"""Support for the Yandex SpeechKit service."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import io
from typing import Any

import grpc
import yandex.cloud.ai.tts.v3.tts_pb2 as tts_pb2
import yandex.cloud.ai.tts.v3.tts_service_pb2_grpc as tts_service_pb2_grpc
from grpc import aio
from homeassistant.components.tts import TextToSpeechEntity, TtsAudioType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.yandex_speechkit.const import (
    CONF_TTS_UNSAFE,
    CONF_TTS_VOICE,
    DEFAULT_LANG,
    DEFAULT_VOICE,
    DOMAIN,
    LOGGER,
    TTS_LANGUAGES,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yandex SpeechKit text-to-speech."""
    async_add_entities([YandexSpeechKitTTSEntity(config_entry)])


class YandexSpeechKitTTSEntity(TextToSpeechEntity):
    """The Yandex SpeechKit TTS entity."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the entity."""
        self._attr_unique_id = config_entry.entry_id
        self._attr_name = config_entry.title
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer="Yandex",
            model="Cloud",
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        self._config_entry = config_entry

    @property
    def supported_languages(self):
        """Return a list of supported languages."""
        return TTS_LANGUAGES

    @property
    def default_language(self):
        """Return the default language."""
        return DEFAULT_LANG

    @property
    def supported_options(self):
        """Return a list of supported options like voice, emotions."""
        return [CONF_TTS_VOICE]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Get TTS audio from Yandex SpeechKit."""
        LOGGER.debug("Starting TTS synthesis for message: %s", message)

        voice = self._config_entry.options.get(CONF_TTS_VOICE, DEFAULT_VOICE)
        unsafe_mode = self._config_entry.options.get(CONF_TTS_UNSAFE, False)

        if len(message) > 249 and not unsafe_mode:
            LOGGER.info(
                "Message is too long (%s characters) and will be truncated",
                len(message),
            )

        request = tts_pb2.UtteranceSynthesisRequest(
            text=message if unsafe_mode else message[:249],
            output_audio_spec=tts_pb2.AudioFormatOptions(
                container_audio=tts_pb2.ContainerAudio(
                    container_audio_type=tts_pb2.ContainerAudio.WAV
                )
            ),
            hints=[
                tts_pb2.Hints(voice=voice),
            ],
            loudness_normalization_type=tts_pb2.UtteranceSynthesisRequest.LUFS,
            unsafe_mode=unsafe_mode,
        )

        cred = grpc.ssl_channel_credentials()
        async with aio.secure_channel("tts.api.cloud.yandex.net:443", cred) as channel:
            stub = tts_service_pb2_grpc.SynthesizerStub(channel)

            api_key = self._config_entry.data[CONF_API_KEY]

            responses = stub.UtteranceSynthesis(
                request,
                metadata=(("authorization", f"Api-Key {api_key}"),),
            )

            try:
                audio = io.BytesIO()
                async for response in responses:
                    if response.audio_chunk.data:
                        audio.write(response.audio_chunk.data)
                    else:
                        LOGGER.warning(
                            "Empty audio chunk received from Yandex SpeechKit"
                        )

                audio.seek(0)
                LOGGER.debug("TTS synthesis completed successfully")
                return ("wav", audio.read())
            except grpc.RpcError as err:
                LOGGER.error("Error occurred during Yandex SpeechKit TTS call: %s", err)
                return None, None
