"""Speech to text using Yandex SpeechKit."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import AsyncGenerator, AsyncIterable, Generator
import grpc

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
import yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc

from .const import STT_LANGUAGES, LOGGER

CHANNELS = 1
RATE = 8000
CHUNK = 4096
RECORD_SECONDS = 30
WAVE_OUTPUT_FILENAME = "audio.wav"


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
        self._config_entry = config_entry

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return STT_LANGUAGES

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        # TODO: add ogg support
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        # TODO: add opus support
        return [AudioCodecs.PCM]

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

        def request_generator(sync_stream):
            # Задайте настройки распознавания.
            recognize_options = stt_pb2.StreamingOptions(
                recognition_model=stt_pb2.RecognitionModelOptions(
                    audio_format=stt_pb2.AudioFormatOptions(
                        raw_audio=stt_pb2.RawAudio(
                            audio_encoding=stt_pb2.RawAudio.LINEAR16_PCM,
                            sample_rate_hertz=metadata.sample_rate,
                            audio_channel_count=1
                        )
                    ),
                    text_normalization=stt_pb2.TextNormalizationOptions(
                        text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
                        profanity_filter=True,
                        literature_text=False
                    ),
                    language_restriction=stt_pb2.LanguageRestrictionOptions(
                        restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
                        # FIXME: metadata.language
                        language_code=['ru-RU']
                    ),
                    audio_processing_type=stt_pb2.RecognitionModelOptions.REAL_TIME
                )
            )

            LOGGER.debug("Sending the message with recognition params...")
            yield stt_pb2.StreamingRequest(session_options=recognize_options)

            LOGGER.debug("Speech recognition...")
            # Распознайте речь по порциям.
            for audio_bytes in sync_stream:
                LOGGER.debug("Sending the next audio chunk...")
                yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=audio_bytes))

        LOGGER.debug("Processing audio stream")
        # Установите соединение с сервером.
        cred = grpc.ssl_channel_credentials()
        channel = grpc.secure_channel("stt.api.cloud.yandex.net:443", cred)
        stub = stt_service_pb2_grpc.RecognizerStub(channel)

        api_key = self._config_entry.data["api_key"]

        # Отправьте данные для распознавания.
        print('1')

        sync_stream = []
        async for audio_bytes in stream:
            sync_stream.append(audio_bytes)

        it = stub.RecognizeStreaming(
            request_generator(sync_stream),
            metadata=(("authorization", f"Api-Key {api_key}"),),
        )
        print('2')

        # Обработайте ответы сервера и выведите результат в консоль.
        alternatives = None
        try:
            for r in it:
                print('3')
                event_type = r.WhichOneof('Event')
                if event_type == 'partial' and len(r.partial.alternatives) > 0:
                    alternatives = [a.text for a in r.partial.alternatives]
                if event_type == 'final':
                    alternatives = [a.text for a in r.final.alternatives]
                if event_type == 'final_refinement':
                    alternatives = [a.text for a in r.final_refinement.normalized_text.alternatives]
                LOGGER.debug(f'type={event_type}, alternatives={alternatives}')
        except Exception as err:
            LOGGER.error("Error occured during: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)

        if alternatives is None:
            return SpeechResult(None, SpeechResultState.ERROR)
        return SpeechResult("".join(alternatives), SpeechResultState.SUCCESS)
