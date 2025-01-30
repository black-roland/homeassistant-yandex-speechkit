"""Speech to text using Yandex SpeechKit."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import AsyncIterable

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
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from speechkit import model_repository
from speechkit.stt import AudioProcessingType, RecognitionModel

from .const import STT_LANGUAGES


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Yandex SpeechKit via config entry."""
    model = model_repository.recognition_model()
    model.model = "general"
    model.language = "ru-RU"
    model.audio_processing_type = AudioProcessingType.Stream
    async_add_entities([YandexSpeechKitSTTEntity(config_entry, model)])


class YandexSpeechKitSTTEntity(SpeechToTextEntity):
    """Yandex STT entity."""

    def __init__(self, config_entry: ConfigEntry, model: RecognitionModel) -> None:
        """Initialize the entity."""
        self._config_entry = config_entry
        self._model = model

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return STT_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV, AudioFormats.OGG]

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
        result = self._model.transcribe(stream)
        print(result)
        # return SpeechResult(
        #     state=SpeechResultState.SUCCESS,
        #     text="",
        # )
