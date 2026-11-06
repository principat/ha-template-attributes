"""Tests for the config and options flow."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.template_attributes.const import (
    CONF_ATTRIBUTES,
    CONF_NAME,
    CONF_STATE_TEMPLATE,
    DOMAIN,
)


async def _start(hass: HomeAssistant, user_input: dict):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    return await hass.config_entries.flow.async_configure(result["flow_id"], user_input)


async def test_flow_creates_entry_with_empty_attribute_list(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 1 + 1 }}"})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Demo"
    assert result["data"][CONF_STATE_TEMPLATE] == "{{ 1 + 1 }}"
    assert result["data"][CONF_ATTRIBUTES] == []


async def test_invalid_template_syntax_is_reported_on_the_field(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 1 + "})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_STATE_TEMPLATE: "invalid_template"}
    assert result["description_placeholders"]["template_error"]


async def test_render_error_is_reported_on_the_field(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 1 / 0 }}"})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_STATE_TEMPLATE: "template_render_error"}


async def test_options_flow_links_to_the_panel_with_this_helper(
    hass: HomeAssistant, make_entry
) -> None:
    entry = make_entry("{{ 1 }}")

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["description_placeholders"]["panel_url"] == (
        f"/template-attributes?entry={entry.entry_id}"
    )


async def test_options_flow_keeps_attributes_defined_in_the_panel(
    hass: HomeAssistant, make_entry
) -> None:
    entry = make_entry("{{ 1 }}")
    hass.config_entries.async_update_entry(
        entry, options={CONF_ATTRIBUTES: [{"name": "a", "template": "x"}]}
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_STATE_TEMPLATE: "{{ 2 }}"}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_STATE_TEMPLATE] == "{{ 2 }}"
    assert entry.options[CONF_ATTRIBUTES] == [{"name": "a", "template": "x"}]
