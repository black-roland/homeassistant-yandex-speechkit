Описание [на русском ниже](#интеграция-yandex-speechkit-для-home-assistant) 👇
<br>
<br>

# Yandex SpeechKit Integration for Home Assistant

[![Add custom repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-yandex-speechkit&category=integration) [![Set up Yandex SpeechKit integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=yandex_speechkit)

This integration brings Yandex SpeechKit's powerful speech-to-text (STT) and text-to-speech (TTS) capabilities to Home Assistant. With support for over 15 languages, high accuracy, and low latency, Yandex SpeechKit enables you to create a unique voice assistant experience in your smart home.

SpeechKit is a cloud service. Fees are charged according to the Yandex Cloud tariffs.

## Features

- **Speech-to-Text (STT):**
  - Recognize speech in [over 15 languages](https://yandex.cloud/en-ru/docs/speechkit/stt/models).
  - High accuracy and fast processing.

- **Text-to-Speech (TTS):**
  - Generate natural-sounding speech.
  - Supports multiple languages and voices.

- **Seamless Integration:**
  - Compatible with [YandexGPT](https://github.com/black-roland/homeassistant-yandexgpt) for advanced conversational AI.
  - Provides TTS capability through the Yandex.Station integration.

## Prerequisites

**Yandex Cloud Account:**

- Create a [service account](https://yandex.cloud/en/docs/iam/concepts/users/service-accounts) with the following roles:
  - `ai.speechkit-tts.user`
  - `ai.speechkit-stt.user`
  - (optional) `ai.languageModels.user` if using YandexGPT integration.
- Generate an [API key](https://yandex.cloud/en/docs/iam/concepts/authorization/api-key) for authentication.

## Installation

1. Add the repository to HACS (Home Assistant Community Store): `https://github.com/black-roland/homeassistant-yandex-speechkit` or use the blue button above
2. Install the custom component through HACS.
3. Restart Home Assistant to complete the installation.

## Configuration

- [Set up the integraion in settings](https://my.home-assistant.io/redirect/config_flow_start/?domain=yandex_speechkit).
- Enter your API key and save the configuration.
- Configure Yandex SpeechKit as an STT and TTS engine for your Voice assistant.

## Donations

If this integration has been useful to you, consider [buying the author a coffee](https://www.donationalerts.com/r/mansmarthome)! Your gratitude is appreciated!

#### Thank you

A huge thank you to everyone who has supported this project! Your contributions make a big difference.

![Thank you](https://github.com/user-attachments/assets/d00d2ad7-6dec-4449-bd0f-0c0a270490fa)

---

# Интеграция Yandex SpeechKit для Home Assistant

[![Добавить репозиторий в HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=black-roland&repository=homeassistant-yandex-speechkit&category=integration) [![Настроить интеграцию](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=yandex_speechkit)

Эта интеграция добавляет в Home Assistant мощные возможности распознавания (STT) и синтеза речи (TTS) от Yandex SpeechKit. С поддержкой более 15 языков, высокой точностью и минимальной задержкой, Yandex SpeechKit позволяет создать уникального голосового ассистента для вашего умного дома.

SpeechKit — это облачный сервис, плата за который взимается в соответствии с тарифами Yandex Cloud. При первой регистрации [можно получить стартовый грант](https://yandex.cloud/ru/docs/getting-started/usage-grant).

## Возможности

- **Распознавание речи (STT):**
  - Поддержка [более 15 языков](https://yandex.cloud/ru/docs/speechkit/stt/models).
  - Высокая точность и быстрая обработка.

- **Синтез речи (TTS):**
  - Генерация естественно звучащей речи из любого входящего текста.
  - Поддержка множества языков и голосов.

- **Бесшовная интеграция:**
  - Может работать вместе с [YandexGPT](https://github.com/black-roland/homeassistant-yandexgpt) для создания продвинутого ассистента.
  - Предоставляет функцию преобразования текста в речь (TTS) через интеграцию с Yandex.Station.

## Подготовка

**Аккаунт Yandex Cloud:**

- Создайте [сервисный аккаунт](https://yandex.cloud/ru/docs/iam/concepts/users/service-accounts) с ролями:
  - `ai.speechkit-tts.user`
  - `ai.speechkit-stt.user`
  - (опционально) `ai.languageModels.user`, если используется интеграция с YandexGPT.
- Сгенерируйте [API-ключ](https://yandex.cloud/ru/docs/iam/concepts/authorization/api-key) для аутентификации.

## Установка

1. Добавьте репозиторий в HACS: `https://github.com/black-roland/homeassistant-yandex-speechkit` или воспользуйтесь синей кнопкой выше.
2. Установите пользовательский компонент через HACS.
3. Перезапустите Home Assistant, чтобы завершить установку.

## Конфигурация

- Добавьте интеграцию в настройках.
- Введите ваш ключ API и сохраните конфигурацию.
- Настройте Yandex SpeechKit в качестве движка распознавания (STT) и синтеза речи (TTS) для вашего голосового помощника.

## Поддержка автора

Если эта интеграция была вам полезна, подумайте о том, чтобы [угостить автора чашечкой кофе](https://mansmarthome.info/donate/#donationalerts)! Ваша благодарность ценится!

#### Благодарности

Огромное спасибо всем, кто поддерживает этот проект! Ваш вклад имеет большое значение.

![Thank you](https://github.com/user-attachments/assets/d00d2ad7-6dec-4449-bd0f-0c0a270490fa)

