"""Config and options flow for Template Attributes.

The flow only covers the *standard sensor* (name, state template, unit, classes, icon). The custom
attributes are edited in the sidebar panel (see ``frontend.py``) because a config flow can neither
show a live value in a section title nor offer add/delete buttons.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_ATTRIBUTES,
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_STATE_CLASS,
    CONF_STATE_TEMPLATE,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PANEL_ENTRY_PARAM,
    PANEL_URL_PATH,
)
from .validation import check_template

_NONE_OPTION = selector.SelectOptionDict(value="", label="—")


class _LenientTemplateSelector(selector.TemplateSelector):
    """Renders like TemplateSelector but leaves syntax errors to our localized validation."""

    def __call__(self, data: Any) -> str:
        return str(data)


def _enum_selector(enum_cls) -> selector.SelectSelector:
    options = [_NONE_OPTION] + [
        selector.SelectOptionDict(value=c.value, label=c.value) for c in enum_cls
    ]
    return selector.SelectSelector(
        selector.SelectSelectorConfig(options=options, mode=selector.SelectSelectorMode.DROPDOWN)
    )


def _schema(defaults: dict[str, Any], with_name: bool) -> vol.Schema:
    fields: dict[Any, Any] = {}
    if with_name:
        fields[vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, ""))] = str
    fields.update(
        {
            vol.Required(
                CONF_STATE_TEMPLATE, default=defaults.get(CONF_STATE_TEMPLATE, "")
            ): _LenientTemplateSelector(),
            vol.Optional(
                CONF_UNIT_OF_MEASUREMENT, default=defaults.get(CONF_UNIT_OF_MEASUREMENT, "")
            ): str,
            vol.Optional(
                CONF_DEVICE_CLASS, default=defaults.get(CONF_DEVICE_CLASS, "")
            ): _enum_selector(SensorDeviceClass),
            vol.Optional(
                CONF_STATE_CLASS, default=defaults.get(CONF_STATE_CLASS, "")
            ): _enum_selector(SensorStateClass),
            vol.Optional(
                CONF_ICON, default=defaults.get(CONF_ICON, "")
            ): selector.IconSelector(),
            vol.Optional(
                CONF_UPDATE_INTERVAL,
                default=defaults.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=1)),
        }
    )
    return vol.Schema(fields)


def _validate(hass, user_input: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    """Localized field errors + description placeholders for the state template."""
    problem = check_template(hass, user_input.get(CONF_STATE_TEMPLATE, ""))
    if problem is None:
        return {}, {}
    code, message = problem
    return {CONF_STATE_TEMPLATE: code}, {"template_error": message}


class TemplateAttributesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create a new Template Attributes helper."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {"template_error": ""}
        if user_input is not None:
            errors, found = _validate(self.hass, user_input)
            placeholders.update(found)
            if not errors:
                data = {**user_input, CONF_ATTRIBUTES: []}
                return self.async_create_entry(title=user_input[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input or {}, with_name=True),
            errors=errors,
            description_placeholders=placeholders,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "TemplateAttributesOptionsFlow":
        return TemplateAttributesOptionsFlow()


class TemplateAttributesOptionsFlow(config_entries.OptionsFlow):
    """Edit the standard sensor settings; attributes stay untouched (they have their own editor)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        current = {**self.config_entry.data, **self.config_entry.options}
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {
            "template_error": "",
            # deep link into the attribute panel with this helper preselected
            "panel_url": (
                f"/{PANEL_URL_PATH}?{PANEL_ENTRY_PARAM}={self.config_entry.entry_id}"
            ),
        }
        if user_input is not None:
            errors, found = _validate(self.hass, user_input)
            placeholders.update(found)
            if not errors:
                # options replace each other wholesale, so carry the attributes over
                return self.async_create_entry(
                    title="",
                    data={**self.config_entry.options, **user_input},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(user_input or current, with_name=False),
            errors=errors,
            description_placeholders=placeholders,
        )
