"""Tests for the websocket API behind the editor panel."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.template_attributes.const import CONF_ATTRIBUTES, DOMAIN


@pytest.fixture
async def client(hass: HomeAssistant, hass_ws_client, make_entry):
    entry = make_entry("{{ 1 }}", [("a", "{{ 2 }}")], unit_of_measurement="W")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry, await hass_ws_client(hass)


async def test_list_returns_definitions_and_entity_id(client) -> None:
    entry, ws = client
    await ws.send_json({"id": 1, "type": f"{DOMAIN}/list"})
    msg = await ws.receive_json()

    assert msg["success"]
    [helper] = msg["result"]
    assert helper["entry_id"] == entry.entry_id
    assert helper["entity_id"] == "sensor.demo"
    assert helper["state_template"] == "{{ 1 }}"
    assert helper["attributes"] == [{"name": "a", "template": "{{ 2 }}"}]


async def test_save_stores_definitions_and_keeps_other_options(
    hass: HomeAssistant, client
) -> None:
    entry, ws = client
    await ws.send_json(
        {
            "id": 1,
            "type": f"{DOMAIN}/save",
            "entry_id": entry.entry_id,
            "state_template": "{{ 5 }}",
            "attributes": [{"name": "b", "template": "{{ state + 1 }}"}],
        }
    )
    msg = await ws.receive_json()
    await hass.async_block_till_done()

    assert msg["result"] == {"ok": True}
    assert entry.options[CONF_ATTRIBUTES] == [{"name": "b", "template": "{{ state + 1 }}"}]
    state = hass.states.get("sensor.demo")
    assert state.state == "5"
    assert state.attributes["b"] == 6
    assert state.attributes["unit_of_measurement"] == "W"


@pytest.mark.parametrize(
    ("attributes", "code"),
    [
        ([{"name": "1bad", "template": "x"}], "invalid_attribute_name"),
        ([{"name": "has space", "template": "x"}], "invalid_attribute_name"),
        ([{"name": "icon", "template": "x"}], "reserved_attribute_name"),
        (
            [{"name": "dup", "template": "x"}, {"name": "dup", "template": "y"}],
            "duplicate_attribute_name",
        ),
        ([{"name": "t", "template": "{{ 1 + "}], "invalid_template"),
        ([{"name": "t", "template": "{{ 1 / 0 }}"}], "template_render_error"),
    ],
)
async def test_save_rejects_bad_attributes_without_changing_anything(
    client, attributes, code
) -> None:
    entry, ws = client
    await ws.send_json(
        {
            "id": 1,
            "type": f"{DOMAIN}/save",
            "entry_id": entry.entry_id,
            "state_template": "{{ 1 }}",
            "attributes": attributes,
        }
    )
    msg = await ws.receive_json()

    assert msg["success"]
    assert msg["result"]["ok"] is False
    error = next(iter(msg["result"]["errors"]["attributes"].values()))
    assert error["code"] == code
    assert CONF_ATTRIBUTES not in entry.options


async def test_save_rejects_bad_state_template(client) -> None:
    entry, ws = client
    await ws.send_json(
        {
            "id": 1,
            "type": f"{DOMAIN}/save",
            "entry_id": entry.entry_id,
            "state_template": "{{ ",
            "attributes": [],
        }
    )
    msg = await ws.receive_json()

    assert msg["result"]["ok"] is False
    assert msg["result"]["errors"]["state_template"]["code"] == "invalid_template"


async def test_save_unknown_entry_is_an_error(client) -> None:
    _, ws = client
    await ws.send_json(
        {
            "id": 1,
            "type": f"{DOMAIN}/save",
            "entry_id": "nope",
            "state_template": "x",
            "attributes": [],
        }
    )
    msg = await ws.receive_json()
    assert not msg["success"]
    assert msg["error"]["code"] == "not_found"
