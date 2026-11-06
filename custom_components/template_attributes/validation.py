"""Validation used by the config and options flow (single source of truth)."""
from __future__ import annotations

import re
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.template import Template

from .const import RESERVED_ATTRIBUTE_NAMES

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

ERR_INVALID_TEMPLATE = "invalid_template"
ERR_RENDER = "template_render_error"
ERR_ATTRIBUTE_INVALID_TEMPLATE = "attribute_invalid_template"
ERR_ATTRIBUTE_RENDER = "attribute_template_render_error"
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


def check_attributes(
    hass: HomeAssistant, attributes: list[dict[str, str]]
) -> tuple[str, str, str] | None:
    """Validate all attributes (name rules, then every template with ``state`` = 0).

    Returns ``(error_code, attribute_name, message)`` for the first problem, or None if fine.
    """
    names = [attr["name"] for attr in attributes]
    name_errors = check_attribute_names(names)
    for name in names:
        if name in name_errors:
            return name_errors[name], name, ""
    for attr in attributes:
        problem = check_template(hass, attr["template"], {"state": 0})
        if problem:
            code = (
                ERR_ATTRIBUTE_INVALID_TEMPLATE
                if problem[0] == ERR_INVALID_TEMPLATE
                else ERR_ATTRIBUTE_RENDER
            )
            return code, attr["name"], problem[1]
    return None
