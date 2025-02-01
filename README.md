# Yandex STT integration for Home Assistant

[![Add custom repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-yandex-speechkit&category=integration) [![Set up Yandex SpeechKit integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=yandex_speechkit)

[Work in progress](https://www.youtube.com/playlist?list=PLtVBPjV2ejLHG70DP8jzbR25Yab3WcaQS). Currently the integration fully supports speech-to-text using Yandex SpeechKit. It's planned to add text-to-speech using Yandex SpeechKit as well.

## Prerequisites

- A [service account](https://yandex.cloud/en/docs/iam/concepts/users/service-accounts) with these roles specified: `ai.speechkit-tts.user`, `ai.speechkit-stt.user`.
- If you're planning to use this integration together with [the YandexGPT integration](https://github.com/black-roland/homeassistant-yandexgpt), you'll need to add `ai.languageModels.user` role as well.
- [An API key](https://yandex.cloud/en/docs/iam/concepts/authorization/api-key).

## Configuration

- [Set up the integraion in settings](https://my.home-assistant.io/redirect/config_flow_start/?domain=yandex_speechkit).
- Configure it as an STT engine for your Assist.
