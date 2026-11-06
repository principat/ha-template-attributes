"""Template Attributes integration."""
from __future__ import annotations

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from .const import DOMAIN, PLATFORMS
from .frontend import async_register_panel
from .websocket_api import async_register_websocket_api

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the websocket API and the editor panel."""
    async_register_websocket_api(hass)
    integration = await async_get_integration(hass, DOMAIN)
    await async_register_panel(hass, str(integration.version))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a helper instance."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # editing options (flow or panel) must take effect without restarting HA
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def _async_reload(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove a helper instance."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
