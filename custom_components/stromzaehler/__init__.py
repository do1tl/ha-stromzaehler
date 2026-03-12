"""Virtueller Stromzähler – Home Assistant Integration."""
from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    CONF_PHASE_A, CONF_PHASE_B, CONF_PHASE_C,
    CONF_METER_BASIS, CONF_PHASE_OFFSET,
)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor"]


def _get_phase_sum(hass: HomeAssistant, data: dict) -> float:
    """Summe der 3 Phasen (nur positive Werte = Bezug vom Netz)."""
    total = 0.0
    for key in (CONF_PHASE_A, CONF_PHASE_B, CONF_PHASE_C):
        entity_id = data.get(key, "")
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        if state is None or state.state in ("unknown", "unavailable"):
            continue
        try:
            total += max(0.0, float(state.state))
        except (ValueError, TypeError):
            pass
    return round(total, 3)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration einrichten."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def handle_set_meter_reading(call: ServiceCall) -> None:
        """Service: Zählerstand neu setzen."""
        value = float(call.data["value"])
        offset = _get_phase_sum(hass, entry.data)
        _LOGGER.info(
            "Zählerstand gesetzt: %.1f kWh (Offset: %.3f kWh)", value, offset
        )
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, CONF_METER_BASIS: value, CONF_PHASE_OFFSET: offset},
        )

    hass.services.async_register(
        DOMAIN,
        "set_meter_reading",
        handle_set_meter_reading,
        schema=vol.Schema({vol.Required("value"): vol.Coerce(float)}),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integration entladen."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        try:
            hass.services.async_remove(DOMAIN, "set_meter_reading")
        except Exception:
            pass
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Sensoren bei Konfig-Änderung neu laden."""
    await hass.config_entries.async_reload(entry.entry_id)
