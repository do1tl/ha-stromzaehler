"""Config Flow für Virtuellen Stromzähler."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_PHASE_A, CONF_PHASE_B, CONF_PHASE_C,
    CONF_SOLAR, CONF_BATT_CHARGE, CONF_BATT_DISCHARGE,
    CONF_METER_BASIS, CONF_PHASE_OFFSET,
)

_ENERGY_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="sensor", device_class="energy")
)
_NUMBER_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=0, max=999999, step=1,
        unit_of_measurement="kWh",
        mode=selector.NumberSelectorMode.BOX,
    )
)


class StromzaehlerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow: Schritt-für-Schritt Einrichtung."""

    VERSION = 1
    _data: dict = {}

    # ── Schritt 1: Phasen + Zählerstand ──────────────────────────────────────
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._data = dict(user_input)
            self._data[CONF_PHASE_OFFSET] = 0.0
            return await self.async_step_solar()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_PHASE_A): _ENERGY_SELECTOR,
                vol.Required(CONF_PHASE_B): _ENERGY_SELECTOR,
                vol.Required(CONF_PHASE_C): _ENERGY_SELECTOR,
                vol.Required(CONF_METER_BASIS, default=0): _NUMBER_SELECTOR,
            }),
        )

    # ── Schritt 2: Solar (optional) ───────────────────────────────────────────
    async def async_step_solar(self, user_input=None):
        if user_input is not None:
            if user_input.get(CONF_SOLAR):
                self._data[CONF_SOLAR] = user_input[CONF_SOLAR]
            return await self.async_step_battery()

        return self.async_show_form(
            step_id="solar",
            data_schema=vol.Schema({
                vol.Optional(CONF_SOLAR): _ENERGY_SELECTOR,
            }),
        )

    # ── Schritt 3: Batterie (optional) ────────────────────────────────────────
    async def async_step_battery(self, user_input=None):
        if user_input is not None:
            if user_input.get(CONF_BATT_CHARGE):
                self._data[CONF_BATT_CHARGE] = user_input[CONF_BATT_CHARGE]
            if user_input.get(CONF_BATT_DISCHARGE):
                self._data[CONF_BATT_DISCHARGE] = user_input[CONF_BATT_DISCHARGE]

            return self.async_create_entry(
                title="Virtueller Stromzähler",
                data=self._data,
            )

        return self.async_show_form(
            step_id="battery",
            data_schema=vol.Schema({
                vol.Optional(CONF_BATT_CHARGE): _ENERGY_SELECTOR,
                vol.Optional(CONF_BATT_DISCHARGE): _ENERGY_SELECTOR,
            }),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return StromzaehlerOptionsFlow(config_entry)


class StromzaehlerOptionsFlow(config_entries.OptionsFlow):
    """Options Flow: Zählerstand aktualisieren."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            value = float(user_input[CONF_METER_BASIS])

            # Aktuelle Phasensumme als neuen Offset speichern
            offset = 0.0
            for key in (CONF_PHASE_A, CONF_PHASE_B, CONF_PHASE_C):
                entity_id = self._entry.data.get(key, "")
                if not entity_id:
                    continue
                state = self.hass.states.get(entity_id)
                if state is None or state.state in ("unknown", "unavailable"):
                    continue
                try:
                    offset += max(0.0, float(state.state))
                except (ValueError, TypeError):
                    pass

            self.hass.config_entries.async_update_entry(
                self._entry,
                data={
                    **self._entry.data,
                    CONF_METER_BASIS: value,
                    CONF_PHASE_OFFSET: round(offset, 3),
                },
            )
            return self.async_create_entry(title="", data={})

        current = self._entry.data.get(CONF_METER_BASIS, 0)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(CONF_METER_BASIS, default=current): _NUMBER_SELECTOR,
            }),
        )
