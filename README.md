# ha-stromzaehler

Virtueller Stromzähler für Home Assistant mit 3-Phasen-Unterstützung.
Funktioniert mit Shelly 3EM, Eastron SDM, Victron und jedem anderen Sensor mit `device_class: energy`.

## Installation

### Schritt 1 – Blueprint importieren

[![Blueprint importieren](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fdo1tl%2Fha-stromzaehler%2Fblob%2Fmain%2Fblueprints%2Fstromzaehler.yaml)

### Schritt 2 – Zwei Helfer anlegen

**Einstellungen → Geräte & Dienste → Helfer → Helfer erstellen → Zahl**

| Name | Entity-ID | Min | Max | Schrittweite | Einheit |
|------|-----------|-----|-----|--------------|---------|
| Zählerstand Basis | `input_number.stromzaehler_basis` | 0 | 999999 | 1 | kWh |
| Zählerstand Offset intern | `input_number.stromzaehler_offset` | 0 | 9999999 | 0.001 | kWh |

### Schritt 3 – Package installieren

1. Datei [`packages/stromzaehler.yaml`](packages/stromzaehler.yaml) herunterladen
2. In `config/packages/` ablegen
3. Die 3 Platzhalter (`sensor.PHASE_A_HIER` etc.) durch deine echten Sensor-IDs ersetzen
4. In `configuration.yaml` eintragen (falls noch nicht vorhanden):
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
5. HA neu starten

### Schritt 4 – Blueprint-Automation einrichten

1. **Einstellungen → Automatisierungen → Blueprint-Automation erstellen**
2. "Virtueller Stromzähler (3-Phasen)" auswählen
3. Die 3 Phasen-Sensoren und beide Helfer aus dem Dropdown auswählen
4. Speichern

### Schritt 5 – Zählerstand eintragen

Im Helper **"Zählerstand Basis"** den aktuellen Zählerstand eintragen.
Ab sofort wird der Verbrauch automatisch weiter gezählt.

### Jährlicher Reset

Einfach den neuen Jahresanfangs-Zählerstand in den Helper eintragen – der Offset wird automatisch neu gesetzt.

---

## Dashboard-Karte

Den Inhalt von [`lovelace/card.yaml`](lovelace/card.yaml) im Lovelace-Editor als manuelle Karte einfügen.

---

## Verfügbare Sensoren nach Installation

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.zahlerstand_aktuell` | Aktueller Zählerstand in kWh |
| `sensor.jahresverbrauch_bisher` | Verbrauch seit letzter Eingabe in kWh |
