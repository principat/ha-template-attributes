"""Tests for the Template Attributes sensor."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.template_attributes.const import CONF_ATTRIBUTES, CONF_STATE_TEMPLATE


async def _setup(hass: HomeAssistant, entry) -> str:
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return "sensor.demo"


async def test_state_and_attributes_are_rendered(hass: HomeAssistant, make_entry) -> None:
    entry = make_entry(
        "{{ 40 + 2 }}",
        [("double", "{{ state * 2 }}"), ("label", "hello"), ("items", "{{ [1, 2, 3] }}")],
    )
    entity_id = await _setup(hass, entry)

    state = hass.states.get(entity_id)
    assert state.state == "42"
    assert state.attributes["double"] == 84  # `state` is available to attribute templates
    assert state.attributes["label"] == "hello"
    assert state.attributes["items"] == [1, 2, 3]  # native types survive


async def test_follows_source_entity(hass: HomeAssistant, make_entry) -> None:
    hass.states.async_set("sensor.source", "10")
    entry = make_entry(
        "{{ states('sensor.source') | float }}",
        [("plus_one", "{{ states('sensor.source') | float + 1 }}")],
    )
    entity_id = await _setup(hass, entry)
    assert hass.states.get(entity_id).attributes["plus_one"] == 11

    hass.states.async_set("sensor.source", "20")
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "20.0"
    assert hass.states.get(entity_id).attributes["plus_one"] == 21


async def test_failing_attribute_keeps_last_value_and_does_not_break_others(
    hass: HomeAssistant, make_entry
) -> None:
    hass.states.async_set("sensor.source", "2")
    entry = make_entry(
        "ok",
        [
            ("fragile", "{{ 10 / (states('sensor.source') | int) }}"),
            ("stable", "{{ 'fine' }}"),
        ],
    )
    entity_id = await _setup(hass, entry)
    assert hass.states.get(entity_id).attributes["fragile"] == 5

    hass.states.async_set("sensor.source", "0")  # division by zero
    await hass.async_block_till_done()
    attrs = hass.states.get(entity_id).attributes
    assert attrs["fragile"] == 5  # last good value kept
    assert attrs["stable"] == "fine"


async def test_options_update_reloads_with_new_attributes(
    hass: HomeAssistant, make_entry
) -> None:
    entry = make_entry("1", [("old", "x")])
    entity_id = await _setup(hass, entry)
    assert "old" in hass.states.get(entity_id).attributes

    hass.config_entries.async_update_entry(
        entry,
        options={
            CONF_STATE_TEMPLATE: "2",
            CONF_ATTRIBUTES: [{"name": "new", "template": "y"}],
        },
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == "2"
    assert "old" not in state.attributes
    assert state.attributes["new"] == "y"


async def test_unit_and_classes_are_applied(hass: HomeAssistant, make_entry) -> None:
    entry = make_entry(
        "{{ 21.5 }}",
        unit_of_measurement="°C",
        device_class="temperature",
        state_class="measurement",
        icon="mdi:thermometer",
    )
    entity_id = await _setup(hass, entry)
    attrs = hass.states.get(entity_id).attributes
    assert attrs["unit_of_measurement"] == "°C"
    assert attrs["device_class"] == "temperature"
    assert attrs["icon"] == "mdi:thermometer"
