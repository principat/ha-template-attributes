"""Constants for the Template Attributes integration."""
from __future__ import annotations

DOMAIN = "template_attributes"
PLATFORMS = ["sensor"]

CONF_NAME = "name"
CONF_STATE_TEMPLATE = "state_template"
CONF_ATTRIBUTES = "attributes"
CONF_ATTRIBUTE_NAME = "name"
CONF_ATTRIBUTE_TEMPLATE = "template"
CONF_UNIT_OF_MEASUREMENT = "unit_of_measurement"
CONF_DEVICE_CLASS = "device_class"
CONF_STATE_CLASS = "state_class"
CONF_ICON = "icon"
CONF_UPDATE_INTERVAL = "update_interval_minutes"

DEFAULT_UPDATE_INTERVAL = 15

# Attribute names Home Assistant itself writes into a state; a custom attribute must not shadow them.
RESERVED_ATTRIBUTE_NAMES = frozenset(
    {
        "friendly_name",
        "unit_of_measurement",
        "device_class",
        "state_class",
        "icon",
        "entity_picture",
        "supported_features",
        "attribution",
        "assumed_state",
        "restored",
        "editable",
        "id",
        "entity_id",
    }
)

PANEL_URL_PATH = "template-attributes"
# query parameter that preselects a helper when the panel is opened
PANEL_ENTRY_PARAM = "entry"
PANEL_ELEMENT = "template-attributes-panel"
PANEL_FILE = "template-attributes-panel.js"
