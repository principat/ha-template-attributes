"""Config and options flow for Template Attributes.

Everything is edited in the standard Home Assistant dialogs:

* **Create**: the standard sensor, then an *attribute step* that is repeated as long as
  "add another attribute" is ticked.
* **Options**: the standard sensor, then one collapsed *section per existing attribute* (title =
  attribute name; change the name to rename it; a switch deletes it), then a tick box to add new
  attributes with the same attribute step.

The sections are named like the attributes, so their titles are the names. Labels of the fields inside
a section cannot come from the translation files (the section keys are dynamic), so those few labels
are chosen in code, by the language of Home Assistant.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector

from .const import (
    CONF_ADD_ANOTHER,
    CONF_ADD_ATTRIBUTE,
    CONF_GO_BACK,
    CONF_ATTRIBUTE_NAME,
    CONF_ATTRIBUTE_TEMPLATE,
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
)
from .validation import check_attributes, check_template

_NONE_OPTION = selector.SelectOptionDict(value="", label="—")

# labels of the fields inside an attribute section (see module docstring)
SECTION_LABELS = {
    "en": {
        "name": "Name",
        "template": "Template",
        "delete": "Delete this attribute (name and template are ignored)",
        "deleted": "Deleted",
        "renamed": "Renamed",
    },
    "de": {
        "name": "Name",
        "template": "Template",
        "delete": "Dieses Attribut löschen (Name und Template werden ignoriert)",
        "deleted": "Gelöscht",
        "renamed": "Umbenannt",
    },
}


def section_labels(language: str | None) -> dict[str, str]:
    return SECTION_LABELS.get((language or "en").split("-")[0].lower(), SECTION_LABELS["en"])


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


def _schema(defaults: dict[str, Any], with_name: bool) -> dict[Any, Any]:
    """The fields of the standard sensor (as a dict, so callers can add more fields)."""
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
    return fields


def _attribute_schema() -> vol.Schema:
    """One attribute to add: name, template, and "add another"."""
    return vol.Schema(
        {
            vol.Optional(CONF_ATTRIBUTE_NAME, default=""): str,
            vol.Optional(CONF_ATTRIBUTE_TEMPLATE, default=""): _LenientTemplateSelector(),
            vol.Optional(CONF_ADD_ANOTHER, default=False): bool,
        }
    )


def options_schema(
    defaults: dict[str, Any],
    attributes: list[dict[str, Any]],
    labels: dict[str, str],
) -> vol.Schema:
    """Standard sensor fields, one collapsed section per attribute, the "add attribute" tick box.

    ``attributes`` items: ``key`` (section key = original name), ``name``, ``template``, ``delete``.
    """
    fields = _schema(defaults, with_name=False)
    for attr in attributes:
        fields[vol.Required(attr["key"])] = section(
            vol.Schema(
                {
                    # first, so it is seen before name and template; a selector renders as a
                    # switch (a plain bool would be a check box)
                    vol.Optional(
                        labels["delete"], default=attr.get("delete", False)
                    ): selector.BooleanSelector(),
                    vol.Required(labels["name"], default=attr["name"]): str,
                    vol.Optional(
                        labels["template"], default=attr["template"]
                    ): _LenientTemplateSelector(),
                }
            ),
            {"collapsed": True},
        )
    fields[vol.Optional(CONF_ADD_ATTRIBUTE, default=bool(defaults.get(CONF_ADD_ATTRIBUTE)))] = bool
    return vol.Schema(fields)


def _validate_state(hass: HomeAssistant, user_input: dict[str, Any]) -> tuple[dict, dict]:
    """Localized field error + placeholders for the state template."""
    problem = check_template(hass, user_input.get(CONF_STATE_TEMPLATE, ""))
    if problem is None:
        return {}, {}
    code, message = problem
    return {CONF_STATE_TEMPLATE: code}, {"template_error": message}


def _names(attributes: list[dict[str, str]]) -> str:
    return ", ".join(a[CONF_ATTRIBUTE_NAME] for a in attributes) or "—"


class _AttributeStepMixin:
    """The repeatable "add an attribute" step, shared by the config and the options flow."""

    hass: HomeAssistant
    _attributes: list[dict[str, str]]

    async def _async_finish(self) -> config_entries.ConfigFlowResult:
        raise NotImplementedError

    async def async_step_attribute(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders = {"attribute": "", "template_error": ""}
        if user_input is not None:
            name = user_input.get(CONF_ATTRIBUTE_NAME, "").strip()
            if not name:  # nothing entered: this is how the step is skipped / finished
                return await self._async_finish()
            candidate = {
                CONF_ATTRIBUTE_NAME: name,
                CONF_ATTRIBUTE_TEMPLATE: user_input.get(CONF_ATTRIBUTE_TEMPLATE, ""),
            }
            problem = check_attributes(self.hass, [*self._attributes, candidate])
            if problem is None:
                self._attributes.append(candidate)
                if not user_input.get(CONF_ADD_ANOTHER):
                    return await self._async_finish()
                user_input = None  # next, empty attribute form
            else:
                code, attribute, message = problem
                errors["base"] = code
                placeholders = {"attribute": attribute, "template_error": message}

        placeholders["attributes"] = _names(self._attributes)
        return self.async_show_form(  # type: ignore[attr-defined]
            step_id="attribute",
            data_schema=self.add_suggested_values_to_schema(  # type: ignore[attr-defined]
                _attribute_schema(), user_input or {}
            ),
            errors=errors,
            description_placeholders=placeholders,
        )


class TemplateAttributesConfigFlow(_AttributeStepMixin, config_entries.ConfigFlow, domain=DOMAIN):
    """Create a new Template Attributes helper."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._attributes: list[dict[str, str]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {"template_error": ""}
        if user_input is not None:
            errors, found = _validate_state(self.hass, user_input)
            placeholders.update(found)
            if not errors:
                self._data = dict(user_input)
                return await self.async_step_attribute()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(_schema(user_input or {}, with_name=True)),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def _async_finish(self) -> config_entries.ConfigFlowResult:
        return self.async_create_entry(
            title=self._data[CONF_NAME],
            data={**self._data, CONF_ATTRIBUTES: self._attributes},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "TemplateAttributesOptionsFlow":
        return TemplateAttributesOptionsFlow()


class TemplateAttributesOptionsFlow(_AttributeStepMixin, config_entries.OptionsFlow):
    """Edit the standard sensor and the existing attributes; add new ones."""

    def __init__(self) -> None:
        self._original: list[dict[str, str]] | None = None
        self._sensor: dict[str, Any] = {}
        self._attributes: list[dict[str, str]] = []
        self._add_attribute = False
        self._view: list[dict[str, Any]] = []
        self._typed: dict[str, Any] = {}

    def _current(self) -> dict[str, Any]:
        return {**self.config_entry.data, **self.config_entry.options}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        current = self._current()
        if self._original is None:
            self._original = [dict(a) for a in current.get(CONF_ATTRIBUTES, [])]
        labels = section_labels(self.hass.config.language)

        # what the user sees now: the stored values, or - after an error - what they typed
        view = [
            {
                "key": a[CONF_ATTRIBUTE_NAME],
                "name": a[CONF_ATTRIBUTE_NAME],
                "template": a[CONF_ATTRIBUTE_TEMPLATE],
            }
            for a in self._original
        ]
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {"template_error": "", "attribute": ""}

        if user_input is not None:
            kept: list[dict[str, str]] = []
            for item in view:
                typed = user_input.get(item["key"], {})
                item["name"] = typed.get(labels["name"], item["name"]).strip()
                item["template"] = typed.get(labels["template"], item["template"])
                item["delete"] = bool(typed.get(labels["delete"], False))
                if not item["delete"]:
                    kept.append(
                        {CONF_ATTRIBUTE_NAME: item["name"], CONF_ATTRIBUTE_TEMPLATE: item["template"]}
                    )

            errors, found = _validate_state(self.hass, user_input)
            placeholders.update(found)
            if not errors:
                problem = check_attributes(self.hass, kept)
                if problem:
                    code, attribute, message = problem
                    errors["base"] = code
                    placeholders.update({"attribute": attribute, "template_error": message})
            if not errors:
                self._sensor = {
                    key: value
                    for key, value in user_input.items()
                    if key not in {i["key"] for i in view} and key != CONF_ADD_ATTRIBUTE
                }
                self._attributes = kept
                self._add_attribute = bool(user_input.get(CONF_ADD_ATTRIBUTE))
                self._view = view
                self._typed = user_input
                # deleting and renaming are only visible after submitting, so confirm them first
                if any(item["delete"] or item["name"] != item["key"] for item in view):
                    return await self.async_step_confirm()
                return await self._async_after_init()

        return self._init_form(view, user_input if user_input is not None else current,
                               errors, placeholders)

    def _init_form(
        self,
        view: list[dict[str, Any]],
        defaults: dict[str, Any],
        errors: dict[str, str],
        placeholders: dict[str, str],
    ) -> config_entries.ConfigFlowResult:
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema(defaults, view, section_labels(self.hass.config.language)),
            errors=errors,
            description_placeholders=placeholders,
        )

    async def _async_after_init(self) -> config_entries.ConfigFlowResult:
        if self._add_attribute:
            return await self.async_step_attribute()
        return await self._async_finish()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show what will be deleted / renamed; nothing is saved before this is submitted."""
        if user_input is not None:
            if user_input.get(CONF_GO_BACK):
                return self._init_form(
                    self._view, self._typed, {}, {"template_error": "", "attribute": ""}
                )
            return await self._async_after_init()

        labels = section_labels(self.hass.config.language)
        deleted = [item["key"] for item in self._view if item["delete"]]
        renamed = [
            f"{item['key']} → {item['name']}"
            for item in self._view
            if not item["delete"] and item["name"] != item["key"]
        ]
        lines = []
        if deleted:
            lines.append(f"- **{labels['deleted']}:** {', '.join(deleted)}")
        if renamed:
            lines.append(f"- **{labels['renamed']}:** {', '.join(renamed)}")
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({vol.Optional(CONF_GO_BACK, default=False): bool}),
            description_placeholders={"changes": "\n".join(lines)},
        )

    async def _async_finish(self) -> config_entries.ConfigFlowResult:
        # options replace each other wholesale, so carry everything over
        return self.async_create_entry(
            title="",
            data={
                **self.config_entry.options,
                **self._sensor,
                CONF_ATTRIBUTES: self._attributes,
            },
        )
