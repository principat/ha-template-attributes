"""Sensor platform for Template Attributes."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.template import Template

from .const import (
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
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the helper entity from the config entry."""
    async_add_entities([TemplateAttributesSensor(hass, entry)])


def _try_number(value: Any) -> Any:
    """Rendered templates return strings, but numbers should stay numbers."""
    if isinstance(value, str):
        try:
            return float(value) if "." in value else int(value)
        except ValueError:
            return value
    return value


class TemplateAttributesSensor(SensorEntity, RestoreEntity):
    """A sensor whose state and custom attributes are each computed from their own template."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        self._unsub_tracking: Any = None
        self._unsub_timer: Any = None
        self._attr_native_value = None
        self._attr_extra_state_attributes: dict[str, Any] = {}
        self._apply_config()

    def _apply_config(self) -> None:
        cfg = {**self._entry.data, **self._entry.options}
        self._attr_name = cfg.get(CONF_NAME)
        self._state_template = Template(cfg.get(CONF_STATE_TEMPLATE, ""), self.hass)
        self._attribute_templates: dict[str, Template] = {
            attr[CONF_ATTRIBUTE_NAME]: Template(attr[CONF_ATTRIBUTE_TEMPLATE], self.hass)
            for attr in cfg.get(CONF_ATTRIBUTES, [])
        }
        self._attr_native_unit_of_measurement = cfg.get(CONF_UNIT_OF_MEASUREMENT) or None
        device_class = cfg.get(CONF_DEVICE_CLASS)
        self._attr_device_class = SensorDeviceClass(device_class) if device_class else None
        state_class = cfg.get(CONF_STATE_CLASS)
        self._attr_state_class = SensorStateClass(state_class) if state_class else None
        self._attr_icon = cfg.get(CONF_ICON) or None
        self._update_interval = cfg.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            self._attr_native_value = last_state.state
            # only keep what is still defined, an attribute deleted in the editor must disappear
            self._attr_extra_state_attributes = {
                name: value
                for name, value in last_state.attributes.items()
                if name in self._attribute_templates
            }
        self._async_recompute()
        self._async_setup_tracking()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_tracking:
            self._unsub_tracking()
        if self._unsub_timer:
            self._unsub_timer()

    @callback
    def _async_setup_tracking(self) -> None:
        """Recompute on state changes of every entity any template reads + periodically."""
        entities: set[str] = set()
        for template in (self._state_template, *self._attribute_templates.values()):
            try:
                info = template.async_render_to_info({"state": None})
                entities.update(info.entities)
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not determine template dependencies for %s", self.entity_id)

        if entities:
            self._unsub_tracking = async_track_state_change_event(
                self.hass, list(entities), self._handle_change
            )
        self._unsub_timer = async_track_time_interval(
            self.hass, self._handle_timer, timedelta(minutes=self._update_interval)
        )

    @callback
    def _handle_change(self, event: Event) -> None:
        self._async_recompute()

    @callback
    def _handle_timer(self, now) -> None:
        self._async_recompute()

    @callback
    def _async_recompute(self) -> None:
        """Render all templates. A failing template keeps its last good value and is logged."""
        try:
            rendered_state = self._state_template.async_render(parse_result=False)
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Error rendering the state template for %s", self.entity_id)
        else:
            self._attr_native_value = _try_number(rendered_state)

        attributes: dict[str, Any] = {}
        for name, template in self._attribute_templates.items():
            try:
                attributes[name] = template.async_render(
                    {"state": self._attr_native_value}, parse_result=True
                )
            except Exception:  # noqa: BLE001
                _LOGGER.exception(
                    "Error rendering attribute '%s' for %s", name, self.entity_id
                )
                if name in self._attr_extra_state_attributes:
                    attributes[name] = self._attr_extra_state_attributes[name]
        self._attr_extra_state_attributes = attributes

        if self.hass is not None and self.entity_id is not None:
            self.async_write_ha_state()
