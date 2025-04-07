"""Speech to text using Yandex SpeechKit."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import AsyncGenerator, AsyncIterable

import grpc
import yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc
from grpc import aio
from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER, STT_LANGUAGES


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yandex SpeechKit via config entry."""
    async_add_entities([YandexSpeechKitSTTEntity(config_entry)])


class YandexSpeechKitSTTEntity(SpeechToTextEntity):
    """Yandex STT entity."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the entity."""

        self._attr_unique_id = f"{config_entry.entry_id}"
        self._attr_name = config_entry.title
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer="Yandex",
            model="Cloud",
            entry_type=dr.DeviceEntryType.SERVICE,
        )
        self._config_entry = config_entry

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return STT_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM, AudioCodecs.OPUS]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return a list of supported bitrates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return a list of supported samplerates."""
        return [
            AudioSampleRates.SAMPLERATE_8000,
            AudioSampleRates.SAMPLERATE_11000,
            AudioSampleRates.SAMPLERATE_16000,
            AudioSampleRates.SAMPLERATE_18900,
            AudioSampleRates.SAMPLERATE_22000,
            AudioSampleRates.SAMPLERATE_32000,
            AudioSampleRates.SAMPLERATE_37800,
            AudioSampleRates.SAMPLERATE_44100,
            AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return a list of supported channels."""
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process an audio stream to STT service."""

        async def request_generator() -> AsyncGenerator[stt_pb2.StreamingRequest, None]:
            recognize_options = self._get_recognition_options(metadata)
            LOGGER.debug("Sending the message with recognition params...")
            yield stt_pb2.StreamingRequest(session_options=recognize_options)

            async for audio_bytes in stream:
                yield stt_pb2.StreamingRequest(
                    chunk=stt_pb2.AudioChunk(data=audio_bytes)
                )

        async def recognize_stream(stub, api_key):
            responses = stub.RecognizeStreaming(
                request_generator(),
                metadata=(("authorization", f"Api-Key {api_key}"),),
            )
            alternatives = []
            async for response in responses:
                if response.WhichOneof("Event") != "final_refinement":
                    continue
                alternatives += [
                    a.text
                    for a in response.final_refinement.normalized_text.alternatives
                ]
            return alternatives

        cred = grpc.ssl_channel_credentials()
        async with aio.secure_channel("stt.api.cloud.yandex.net:443", cred) as channel:
            stub = stt_service_pb2_grpc.RecognizerStub(channel)
            api_key = self._config_entry.data["api_key"]
            try:
                alternatives = await recognize_stream(stub, api_key)
                if not alternatives:
                    return SpeechResult(None, SpeechResultState.ERROR)
                return SpeechResult(" ".join(alternatives), SpeechResultState.SUCCESS)
            except grpc.RpcError as err:
                LOGGER.error("Error occurred during speech recognition: %s", err)
                return SpeechResult(None, SpeechResultState.ERROR)

    def _get_recognition_options(
        self, metadata: SpeechMetadata
    ) -> stt_pb2.StreamingOptions:
        """Get recognition options based on metadata."""
        return stt_pb2.StreamingOptions(
            recognition_model=stt_pb2.RecognitionModelOptions(
                audio_format=(
                    stt_pb2.AudioFormatOptions(
                        container_audio=stt_pb2.ContainerAudio(
                            container_audio_type=stt_pb2.ContainerAudio.OGG_OPUS,
                        )
                    )
                    if metadata.codec == AudioCodecs.OPUS
                    else stt_pb2.AudioFormatOptions(
                        raw_audio=stt_pb2.RawAudio(
                            audio_encoding=stt_pb2.RawAudio.LINEAR16_PCM,
                            sample_rate_hertz=metadata.sample_rate,
                            audio_channel_count=1,
                        )
                    )
                ),
                text_normalization=stt_pb2.TextNormalizationOptions(
                    text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
                    profanity_filter=False,
                    literature_text=True,
                ),
                language_restriction=stt_pb2.LanguageRestrictionOptions(
                    restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
                    language_code=[metadata.language],
                ),
                audio_processing_type=stt_pb2.RecognitionModelOptions.REAL_TIME,
            )
        )
