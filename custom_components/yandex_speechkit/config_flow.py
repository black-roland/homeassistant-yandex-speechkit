"""Config flow for Yandex SpeechKit integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.media_player.const import DOMAIN as MEDIA_DOMAIN
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_PROXY_MEDIA_TYPE,
    CONF_PROXY_SPEAKER,
    CONF_TTS_UNSAFE,
    CONF_TTS_VOICE,
    DEFAULT_VOICE,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_KEY): str,
    }
)


class YandexSpeechKitConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Yandex SpeechKit."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialize config flow."""
        self.api_key: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        if user_input is not None:
            # TODO: Validate input
            return self.async_create_entry(
                title="Yandex SpeechKit",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return YandexSpeechKitOptionsFlow()


class YandexSpeechKitOptionsFlow(OptionsFlow):
    """Yandex SpeechKit options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        schema = self.yandex_speechkit_config_option_schema()
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )

    def yandex_speechkit_config_option_schema(self) -> vol.Schema:
        """Yandex SpeechKit options schema."""

        tts_schema = vol.Schema(
            {
                vol.Optional(CONF_TTS_VOICE, default=DEFAULT_VOICE): str,
                vol.Optional(CONF_TTS_UNSAFE, default=False): bool,
            }
        )

        proxy_schema = vol.Schema(
            {
                vol.Optional(CONF_PROXY_SPEAKER): EntitySelector(
                    EntitySelectorConfig(domain=[MEDIA_DOMAIN])
                ),
                vol.Optional(CONF_PROXY_MEDIA_TYPE, default="tts"): SelectSelector(
                    SelectSelectorConfig(
                        mode=SelectSelectorMode.DROPDOWN,
                        options=["tts", "text", "dialog"],
                    )
                ),
            }
        )

        return self.add_suggested_values_to_schema(
            vol.Schema(
                {
                    **tts_schema.schema,
                    **proxy_schema.schema,
                }
            ),
            self.config_entry.options,
        )
