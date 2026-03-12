"""Sensor-Plattform für Virtuellen Stromzähler."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_PHASE_A, CONF_PHASE_B, CONF_PHASE_C,
    CONF_PHASE_A_RETURNED, CONF_PHASE_B_RETURNED, CONF_PHASE_C_RETURNED,
    CONF_SOLAR, CONF_BATT_CHARGE, CONF_BATT_DISCHARGE, CONF_BATT_NET,
    CONF_METER_BASIS, CONF_PHASE_OFFSET,
)

_LOGGER = logging.getLogger(__name__)


def _val(hass: HomeAssistant, entity_id: str | None) -> float:
    """Sicherer float-Wert aus Entity-State. Wh wird automatisch in kWh umgerechnet."""
    if not entity_id:
        return 0.0
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable", ""):
        return 0.0
    try:
        v = float(state.state)
        if state.attributes.get("unit_of_measurement") == "Wh":
            v /= 1000.0
        return v
    except (ValueError, TypeError):
        return 0.0


def _val_list(hass: HomeAssistant, entity_ids: list | str | None) -> float:
    """Summe über eine Liste von Entity-IDs (oder einzelne ID, rückwärtskompatibel)."""
    if not entity_ids:
        return 0.0
    if isinstance(entity_ids, str):
        return _val(hass, entity_ids)
    return sum(_val(hass, eid) for eid in entity_ids)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Sensoren anlegen."""
    sensors: list[StromzaehlerBaseSensor] = [
        PhasenGesamtSensor(entry),
        ZaehlerstandSensor(entry),
        JahresverbrauchSensor(entry),
        EinspeisungSensor(entry),
    ]

    if entry.data.get(CONF_SOLAR):
        sensors.append(SolarEigenverbrauchSensor(entry))
        sensors.append(EingespartSensor(entry))

    has_batt = (
        (entry.data.get(CONF_BATT_CHARGE) and entry.data.get(CONF_BATT_DISCHARGE))
        or entry.data.get(CONF_BATT_NET)
    )
    if has_batt:
        sensors.append(BatterieEigenverbrauchSensor(entry))

    async_add_entities(sensors)


# ── Basis-Sensor ──────────────────────────────────────────────────────────────

class StromzaehlerBaseSensor(SensorEntity):
    """Gemeinsame Basis für alle Stromzähler-Sensoren."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "kWh"
    _attr_suggested_display_precision = 3
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{self._sensor_key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Virtueller Stromzähler",
            manufacturer="do1tl",
            model="Stromzähler",
            configuration_url="https://github.com/do1tl/ha-stromzaehler",
        )

    @property
    def _sensor_key(self) -> str:
        raise NotImplementedError

    def _tracked_entities(self) -> list[str]:
        entities = [
            self._entry.data[CONF_PHASE_A],
            self._entry.data[CONF_PHASE_B],
            self._entry.data[CONF_PHASE_C],
        ]
        for key in (CONF_PHASE_A_RETURNED, CONF_PHASE_B_RETURNED, CONF_PHASE_C_RETURNED):
            if self._entry.data.get(key):
                entities.append(self._entry.data[key])
        return entities

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                self._tracked_entities(),
                self._on_state_change,
            )
        )
        self._entry.async_on_unload(
            self._entry.add_update_listener(self._on_config_update)
        )

    @callback
    def _on_state_change(self, event) -> None:
        self.async_write_ha_state()

    async def _on_config_update(self, hass, entry) -> None:
        self._entry = entry
        self.async_write_ha_state()

    # ── Hilfsmethoden ─────────────────────────────────────────────────────────

    def _bezug(self) -> float:
        """Netzbezug in kWh. Immer positive Phasenwerte summiert."""
        return sum(
            max(0.0, _val(self.hass, self._entry.data[k]))
            for k in (CONF_PHASE_A, CONF_PHASE_B, CONF_PHASE_C)
        )

    def _einspeisung(self) -> float:
        """
        Einspeisung ins Netz in kWh (positiver Wert).
        Wenn separate 'energy_returned' Sensoren konfiguriert: diese summieren.
        Sonst: negative Phasenwerte (bidirektionaler Sensor) invertieren.
        """
        returned_keys = (
            (CONF_PHASE_A_RETURNED, CONF_PHASE_A),
            (CONF_PHASE_B_RETURNED, CONF_PHASE_B),
            (CONF_PHASE_C_RETURNED, CONF_PHASE_C),
        )
        total = 0.0
        for ret_key, phase_key in returned_keys:
            if self._entry.data.get(ret_key):
                # Separater Einspeise-Sensor (z.B. Shelly energy_returned)
                total += max(0.0, _val(self.hass, self._entry.data[ret_key]))
            else:
                # Fallback: negative Werte des Phasen-Sensors
                total += max(0.0, _val(self.hass, self._entry.data[phase_key]) * -1)
        return total


# ── Konkrete Sensoren ─────────────────────────────────────────────────────────

class PhasenGesamtSensor(StromzaehlerBaseSensor):
    _sensor_key = "phasen_gesamt"
    _attr_name = "Phasen Gesamt (Bezug)"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:sigma"

    @property
    def native_value(self) -> float:
        return round(self._bezug(), 3)


class ZaehlerstandSensor(StromzaehlerBaseSensor):
    _sensor_key = "zaehlerstand"
    _attr_name = "Zählerstand aktuell"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    @property
    def native_value(self) -> float:
        basis  = self._entry.data.get(CONF_METER_BASIS, 0.0)
        offset = self._entry.data.get(CONF_PHASE_OFFSET, 0.0)
        bezug  = self._bezug()
        return round(max(basis + bezug - offset, basis), 3)


class JahresverbrauchSensor(StromzaehlerBaseSensor):
    _sensor_key = "jahresverbrauch"
    _attr_name = "Jahresverbrauch Bezug"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:transmission-tower-import"

    @property
    def native_value(self) -> float:
        offset = self._entry.data.get(CONF_PHASE_OFFSET, 0.0)
        return round(max(self._bezug() - offset, 0.0), 3)


class EinspeisungSensor(StromzaehlerBaseSensor):
    _sensor_key = "einspeisung"
    _attr_name = "Einspeisung gesamt"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:transmission-tower-export"

    @property
    def native_value(self) -> float:
        return round(self._einspeisung(), 3)


class SolarEigenverbrauchSensor(StromzaehlerBaseSensor):
    _sensor_key = "solar_eigenverbrauch"
    _attr_name = "Solar Eigenverbrauch"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:solar-power"

    def _tracked_entities(self) -> list[str]:
        entities = super()._tracked_entities()
        if self._entry.data.get(CONF_SOLAR):
            entities.append(self._entry.data[CONF_SOLAR])
        return entities

    @property
    def native_value(self) -> float:
        solar = _val(self.hass, self._entry.data.get(CONF_SOLAR))
        return round(max(solar - self._einspeisung(), 0.0), 3)


class EingespartSensor(StromzaehlerBaseSensor):
    _sensor_key = "eingespart"
    _attr_name = "Eingespart gesamt"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:piggy-bank"

    def _tracked_entities(self) -> list[str]:
        entities = super()._tracked_entities()
        for key in (CONF_SOLAR, CONF_BATT_DISCHARGE, CONF_BATT_NET):
            val = self._entry.data.get(key)
            if not val:
                continue
            if isinstance(val, list):
                entities.extend(val)
            else:
                entities.append(val)
        return entities

    @property
    def native_value(self) -> float:
        solar = _val(self.hass, self._entry.data.get(CONF_SOLAR))
        eigenverbrauch = max(solar - self._einspeisung(), 0.0)
        net_ids = self._entry.data.get(CONF_BATT_NET)
        if net_ids:
            batt_discharge = max(-_val_list(self.hass, net_ids), 0.0)
        else:
            batt_discharge = _val_list(self.hass, self._entry.data.get(CONF_BATT_DISCHARGE))
        return round(eigenverbrauch + batt_discharge, 3)


class BatterieEigenverbrauchSensor(StromzaehlerBaseSensor):
    _sensor_key = "batterie_eigenverbrauch"
    _attr_name = "Batterie Eigenverbrauch"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery-charging"

    def _tracked_entities(self) -> list[str]:
        entities = []
        for key in (CONF_BATT_NET, CONF_BATT_CHARGE, CONF_BATT_DISCHARGE):
            val = self._entry.data.get(key)
            if not val:
                continue
            if isinstance(val, list):
                entities.extend(val)
            else:
                entities.append(val)
        return entities

    def _batt_charge_discharge(self) -> tuple[float, float]:
        """Gibt (Ladung, Entladung) in kWh zurück."""
        net_ids = self._entry.data.get(CONF_BATT_NET)
        if net_ids:
            net = _val_list(self.hass, net_ids)
            return (max(net, 0.0), max(-net, 0.0))
        charge    = _val_list(self.hass, self._entry.data.get(CONF_BATT_CHARGE))
        discharge = _val_list(self.hass, self._entry.data.get(CONF_BATT_DISCHARGE))
        return (charge, discharge)

    @property
    def native_value(self) -> float:
        charge, discharge = self._batt_charge_discharge()
        return round(max(discharge - charge, 0.0), 3)
