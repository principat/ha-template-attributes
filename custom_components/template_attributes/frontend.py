"""Serves the attribute editor panel (sidebar entry "Template Attributes").

The panel (``www/template-attributes-panel.js``) is plain JavaScript without a build step and only
talks to the integration through the websocket API in ``websocket_api.py``.
"""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import PANEL_ELEMENT, PANEL_FILE, PANEL_URL_PATH

_LOGGER = logging.getLogger(__name__)

_BUNDLE = Path(__file__).parent / "www" / PANEL_FILE
_STATIC_URL = f"/{PANEL_URL_PATH}-static/{PANEL_FILE}"
_REGISTERED_KEY = "template_attributes_panel_registered"


async def async_register_panel(hass: HomeAssistant, version: str) -> None:
    """Expose the panel module and add it to the sidebar. Never raises."""
    if hass.data.get(_REGISTERED_KEY):
        return
    if not _BUNDLE.is_file():
        _LOGGER.debug("Panel bundle not found at %s", _BUNDLE)
        return
    if getattr(hass, "http", None) is None or "frontend" not in hass.config.components:
        _LOGGER.debug("HTTP/frontend not available, skipping the attribute panel")
        return
    try:
        from homeassistant.components.http import StaticPathConfig
        from homeassistant.components.panel_custom import async_register_panel as register

        await hass.http.async_register_static_paths(
            [StaticPathConfig(_STATIC_URL, str(_BUNDLE), cache_headers=False)]
        )
        await register(
            hass,
            webcomponent_name=PANEL_ELEMENT,
            frontend_url_path=PANEL_URL_PATH,
            module_url=f"{_STATIC_URL}?v={version}",
            sidebar_title="Template Attributes",
            sidebar_icon="mdi:tag-multiple",
            require_admin=True,
        )
    except Exception:  # noqa: BLE001 - the panel is optional, never break the integration
        _LOGGER.exception("Could not register the attribute panel")
        return
    hass.data[_REGISTERED_KEY] = True
