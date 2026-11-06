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
# options flow: tick to add a new attribute after saving / "add another" on the attribute step
CONF_ADD_ATTRIBUTE = "add_attribute"
CONF_ADD_ANOTHER = "add_another"
# options flow confirm step: go back to the form instead of applying deletions / renames
CONF_GO_BACK = "go_back"

DEFAULT_UPDATE_INTERVAL = 15

# Attribute names Home Assistant itself writes into a state; a custom attribute must not shadow them.
# The last three are form fields of the options flow: an attribute is a form *section* named like
# the attribute, so it must not collide with a top-level field.
RESERVED_ATTRIBUTE_NAMES = frozenset(
    {
        "state_template",
        "update_interval_minutes",
        "add_attribute",
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

