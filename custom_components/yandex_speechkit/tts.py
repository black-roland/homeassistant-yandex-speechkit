"""Support for the Yandex SpeechKit service."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import io
import os
from typing import Any

import grpc
import yandex.cloud.ai.tts.v3.tts_pb2 as tts_pb2
import yandex.cloud.ai.tts.v3.tts_service_pb2_grpc as tts_service_pb2_grpc
from grpc import aio
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_CONTENT_ID,
    ATTR_MEDIA_CONTENT_TYPE,
)
from homeassistant.components.media_player.const import DOMAIN as MEDIA_DOMAIN
from homeassistant.components.media_player.const import SERVICE_PLAY_MEDIA
from homeassistant.components.tts import (
    ATTR_AUDIO_OUTPUT,
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, CONF_API_KEY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PROXY_MEDIA_TYPE,
    CONF_PROXY_SPEAKER,
    CONF_TTS_UNSAFE,
    DEFAULT_LANG,
    DEFAULT_OUTPUT_CONTAINER,
    DEFAULT_VOICE,
    DOMAIN,
    LOGGER,
    TTS_LANGUAGES,
    TTS_OUTPUT_CONTAINERS,
    TTS_VOICES,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yandex SpeechKit text-to-speech."""
    entities: list[TextToSpeechEntity] = [YandexSpeechKitTTSEntity(config_entry)]

    if config_entry.options.get(CONF_PROXY_SPEAKER):
        entities.append(YandexStationTTSProxyEntity(hass, config_entry))

    async_add_entities(entities)


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
    def supported_options(self) -> list[str]:
        """Return list of supported options like voice, emotion."""
        return [ATTR_VOICE, ATTR_AUDIO_OUTPUT]

    @property
    def default_options(self) -> dict[str, Any]:
        """Return a dict include default options."""
        return {
            ATTR_VOICE: DEFAULT_VOICE,
            ATTR_AUDIO_OUTPUT: DEFAULT_OUTPUT_CONTAINER,
        }

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return a list of supported voices for a language."""
        if not (voices := TTS_VOICES.get(language)):
            return None
        return [Voice(voice, voice) for voice in voices]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Get TTS audio from Yandex SpeechKit."""
        LOGGER.debug("Starting TTS synthesis for message: %s", message)

        output_container = options[ATTR_AUDIO_OUTPUT]
        container_audio_type = TTS_OUTPUT_CONTAINERS.get(
            output_container, TTS_OUTPUT_CONTAINERS[DEFAULT_OUTPUT_CONTAINER]
        )
        voice = options[ATTR_VOICE]
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
                    container_audio_type=container_audio_type
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
                return (output_container, audio.read())
            except grpc.RpcError as err:
                LOGGER.error("Error occurred during Yandex SpeechKit TTS call: %s", err)
                return None, None


class YandexStationTTSProxyEntity(TextToSpeechEntity):
    """The Yandex.Station TTS proxy entity."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        self._attr_unique_id = f"{config_entry.entry_id}_yandex_station_tts_proxy"
        self._attr_name = "Yandex.Station proxy"
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer="AlexxIT",
            model="Yandex.Station",
            entry_type=dr.DeviceEntryType.SERVICE,
        )

        self._hass = hass
        self._config_entry = config_entry

    @property
    def supported_languages(self):
        """Return a list of supported languages."""
        return TTS_LANGUAGES

    @property
    def default_language(self):
        """Return the default language."""
        return DEFAULT_LANG

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Send text to the configured Yandex.Station."""
        if not self._config_entry.options.get(CONF_PROXY_SPEAKER):
            LOGGER.error("No speaker configured for Yandex.Station TTS proxy")
            return (None, None)

        LOGGER.debug("Proxying TTS request to Yandex.Station...")
        try:
            data = {
                ATTR_MEDIA_CONTENT_ID: message,
                ATTR_MEDIA_CONTENT_TYPE: self._config_entry.options.get(
                    CONF_PROXY_MEDIA_TYPE, "tts"
                ),
                ATTR_ENTITY_ID: self._config_entry.options.get(CONF_PROXY_SPEAKER),
            }
            await self._hass.services.async_call(
                MEDIA_DOMAIN, SERVICE_PLAY_MEDIA, data, blocking=True
            )
        except Exception as e:
            LOGGER.error("Error proxying TTS request to Yandex.Station: %s", e)
            return (None, None)

        def _read_empty_wav() -> TtsAudioType:
            try:
                LOGGER.debug("Returning an empty.wav...")
                filename = os.path.join(os.path.dirname(__file__), "empty.wav")
                with open(filename, "rb") as file:
                    empty = file.read()
                    return ("wav", empty)
            except OSError:
                LOGGER.error("Error reading empty.wav")
                return (None, None)

        return await self.hass.async_add_executor_job(_read_empty_wav)
