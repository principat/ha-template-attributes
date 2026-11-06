"""Websocket API used by the attribute editor panel."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_ATTRIBUTE_NAME,
    CONF_ATTRIBUTE_TEMPLATE,
    CONF_ATTRIBUTES,
    CONF_STATE_TEMPLATE,
    DOMAIN,
)
from .validation import validate_definition

_REGISTERED_KEY = "template_attributes_ws_registered"

_ATTRIBUTE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ATTRIBUTE_NAME): str,
        vol.Required(CONF_ATTRIBUTE_TEMPLATE): str,
    }
)


@callback
def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register the commands (once)."""
    if hass.data.get(_REGISTERED_KEY):
        return
    websocket_api.async_register_command(hass, ws_list)
    websocket_api.async_register_command(hass, ws_save)
    hass.data[_REGISTERED_KEY] = True


def _effective(entry) -> dict[str, Any]:
    """Merge data + options (options win)."""
    return {**entry.data, **entry.options}


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/list"})
@websocket_api.require_admin
@callback
def ws_list(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """All helpers with their state template and attribute definitions."""
    registry = er.async_get(hass)
    helpers = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        cfg = _effective(entry)
        helpers.append(
            {
                "entry_id": entry.entry_id,
                "title": entry.title,
                "entity_id": registry.async_get_entity_id("sensor", DOMAIN, entry.entry_id),
                CONF_STATE_TEMPLATE: cfg.get(CONF_STATE_TEMPLATE, ""),
                CONF_ATTRIBUTES: list(cfg.get(CONF_ATTRIBUTES, [])),
            }
        )
    connection.send_result(msg["id"], helpers)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/save",
        vol.Required("entry_id"): str,
        vol.Required(CONF_STATE_TEMPLATE): str,
        vol.Required(CONF_ATTRIBUTES): [_ATTRIBUTE_SCHEMA],
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    """Validate and store state template + attributes.

    Validation problems are a normal result (``ok: false`` + ``errors``), not a websocket error,
    so the panel can show them next to the offending field.
    """
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Unknown helper")
        return

    attributes = [
        {
            CONF_ATTRIBUTE_NAME: attr[CONF_ATTRIBUTE_NAME],
            CONF_ATTRIBUTE_TEMPLATE: attr[CONF_ATTRIBUTE_TEMPLATE],
        }
        for attr in msg[CONF_ATTRIBUTES]
    ]
    errors = validate_definition(hass, msg[CONF_STATE_TEMPLATE], attributes)
    if errors:
        connection.send_result(msg["id"], {"ok": False, "errors": errors})
        return

    # keep the other options (unit, device class, ...) - only these two keys belong to the panel
    hass.config_entries.async_update_entry(
        entry,
        options={
            **entry.options,
            CONF_STATE_TEMPLATE: msg[CONF_STATE_TEMPLATE],
            CONF_ATTRIBUTES: attributes,
        },
    )
    connection.send_result(msg["id"], {"ok": True})
