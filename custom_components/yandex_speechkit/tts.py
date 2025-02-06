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
from homeassistant.components.tts import Provider, TextToSpeechEntity, TtsAudioType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from custom_components.yandex_speechkit.const import DOMAIN, LOGGER


async def async_get_engine(hass, config_entry, discovery_info=None):
    """Set up Yandex SpeechKit component."""
    return YandexSpeechKitTTSProvider(config_entry)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yandex SpeechKit text-to-speech."""
    async_add_entities([YandexSpeechKitTTSEntity(config_entry)])


class BaseYandexSpeechProvider:
    """The Yandex SpeechKit base provider."""

    def __init__(self, config_entry):
        """Init Yandex SpeechKit service."""
        self._config_entry = config_entry

    @property
    def default_language(self):
        """Return the default language."""
        return "ru-RU"

    @property
    def supported_languages(self):
        """Return list of supported languages."""
        return ["ru-RU"]

    @property
    def supported_options(self):
        """Return list of supported options like voice, emotion."""
        return ["voice"]

    async def _async_get_tts_audio(self, message, language, options):
        """Load TTS from Yandex Cloud."""
        LOGGER.debug("Starting TTS synthesis for message: %s", message)
        request = tts_pb2.UtteranceSynthesisRequest(
            text=message,
            output_audio_spec=tts_pb2.AudioFormatOptions(
                container_audio=tts_pb2.ContainerAudio(
                    container_audio_type=tts_pb2.ContainerAudio.WAV
                )
            ),
            loudness_normalization_type=tts_pb2.UtteranceSynthesisRequest.LUFS,
        )

        cred = grpc.ssl_channel_credentials()
        async with aio.secure_channel("tts.api.cloud.yandex.net:443", cred) as channel:
            LOGGER.debug("Channel created")
            stub = tts_service_pb2_grpc.SynthesizerStub(channel)

            api_key = self._config_entry.data["api_key"]

            responses = stub.UtteranceSynthesis(
                request, metadata=(("authorization", f"Api-Key {api_key}"),),
            )
            LOGGER.debug("Received responses from Yandex SpeechKit")

            audio = io.BytesIO()
            async for response in responses:
                if response.audio_chunk.data:
                    audio.write(response.audio_chunk.data)
                else:
                    LOGGER.warning("Empty audio chunk received from Yandex SpeechKit")

            audio.seek(0)
            LOGGER.debug("TTS synthesis completed successfully")
            return ("wav", audio.read())


class YandexSpeechKitTTSEntity(BaseYandexSpeechProvider, TextToSpeechEntity):
    """The Yandex SpeechKit TTS entity."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the entity."""
        super().__init__(config_entry)
        self._attr_unique_id = config_entry.entry_id
        self._attr_name = config_entry.title
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer="Yandex",
            model="Cloud",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Get TTS audio from Yandex SpeechKit."""
        try:
            return await self._async_get_tts_audio(message, language, options)
        except grpc.RpcError as err:
            LOGGER.error("Error occurred during Yandex SpeechKit TTS call: %s", err)
            return None, None


class YandexSpeechKitTTSProvider(BaseYandexSpeechProvider, Provider):
    """The Yandex SpeechKit TTS provider."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Init Yandex SpeechKit service."""
        super().__init__(config_entry)
        LOGGER.debug(config_entry.title)
        LOGGER.debug(config_entry)
        self.name = config_entry.title

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Get TTS audio from Yandex SpeechKit."""
        try:
            return await self._async_get_tts_audio(message, language, options)
        except grpc.RpcError as err:
            LOGGER.error("Error occurred during Yandex SpeechKit TTS call: %s", err)
            return None, None
