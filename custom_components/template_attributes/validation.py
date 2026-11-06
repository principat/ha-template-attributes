"""Validation shared by the config flow and the websocket API (single source of truth)."""
from __future__ import annotations

import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

from .const import (
    CONF_ATTRIBUTE_NAME,
    CONF_ATTRIBUTE_TEMPLATE,
    RESERVED_ATTRIBUTE_NAMES,
)

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ERR_INVALID_TEMPLATE = "invalid_template"
ERR_RENDER = "template_render_error"
ERR_INVALID_NAME = "invalid_attribute_name"
ERR_RESERVED_NAME = "reserved_attribute_name"
ERR_DUPLICATE_NAME = "duplicate_attribute_name"


def check_template(
    hass: HomeAssistant, value: str, variables: dict[str, Any] | None = None
) -> tuple[str, str] | None:
    """Syntax check plus one test render. Returns (error_code, message) or None if fine."""
    if not value:
        return None
    template = Template(value, hass)
    try:
        template.ensure_valid()
    except Exception as err:  # noqa: BLE001
        return ERR_INVALID_TEMPLATE, str(err)
    try:
        template.async_render(variables or {}, parse_result=False)
    except Exception as err:  # noqa: BLE001
        return ERR_RENDER, str(err)
    return None


def check_attribute_names(names: list[str]) -> dict[str, str]:
    """Map attribute name -> error code for every unusable name."""
    errors: dict[str, str] = {}
    seen: set[str] = set()
    for name in names:
        if not _NAME_RE.match(name):
            errors[name] = ERR_INVALID_NAME
        elif name in RESERVED_ATTRIBUTE_NAMES:
            errors[name] = ERR_RESERVED_NAME
        elif name in seen:
            errors[name] = ERR_DUPLICATE_NAME
        seen.add(name)
    return errors


def validate_definition(
    hass: HomeAssistant, state_template: str, attributes: list[dict[str, str]]
) -> dict[str, Any]:
    """Validate state template + attributes.

    Returns {} if everything is fine, otherwise
    ``{"state_template": {code, message}, "attributes": {name: {code, message}}}``
    (only the failing parts are present).
    """
    errors: dict[str, Any] = {}

    problem = check_template(hass, state_template)
    if problem:
        errors["state_template"] = {"code": problem[0], "message": problem[1]}

    names = [attr[CONF_ATTRIBUTE_NAME] for attr in attributes]
    attribute_errors: dict[str, dict[str, str]] = {
        name: {"code": code, "message": ""}
        for name, code in check_attribute_names(names).items()
    }
    for attr in attributes:
        name = attr[CONF_ATTRIBUTE_NAME]
        if name in attribute_errors:
            continue
        problem = check_template(hass, attr[CONF_ATTRIBUTE_TEMPLATE], {"state": 0})
        if problem:
            attribute_errors[name] = {"code": problem[0], "message": problem[1]}
    if attribute_errors:
        errors["attributes"] = attribute_errors
    return errors
