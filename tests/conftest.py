"""Shared fixtures for the Template Attributes tests."""
from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.template_attributes.const import (
    CONF_ATTRIBUTE_NAME,
    CONF_ATTRIBUTE_TEMPLATE,
    CONF_ATTRIBUTES,
    CONF_NAME,
    CONF_STATE_TEMPLATE,
    DOMAIN,
)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Automatically make custom_components/ available for every test."""
    yield


@pytest.fixture
def make_entry(hass):
    """Create + add a config entry; attributes are (name, template) pairs."""

    def _make(state_template="{{ 42 }}", attributes=(), **extra) -> MockConfigEntry:
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Demo",
            data={
                CONF_NAME: "Demo",
                CONF_STATE_TEMPLATE: state_template,
                CONF_ATTRIBUTES: [
                    {CONF_ATTRIBUTE_NAME: n, CONF_ATTRIBUTE_TEMPLATE: t} for n, t in attributes
                ],
                **extra,
            },
        )
        entry.add_to_hass(hass)
        return entry

    return _make
