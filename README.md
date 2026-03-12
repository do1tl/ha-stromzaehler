# ha-stromzaehler

Vollständige Energiebilanz für Home Assistant mit:
- **3-Phasen-Sensor** (Shelly 3EM oder ähnliches)
- **Solaranlage** (Hoymiles, SMA, Fronius, ...)
- **Batteriespeicher** optional (Victron, ...)
- **Manuellem Zählerstand** – jedes Jahr neu eintragen

## Berechnete Sensoren

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.zahlerstand_aktuell` | Aktueller Zählerstand in kWh |
| `sensor.jahresverbrauch_bezug` | Bezug vom Netz seit letzter Eingabe |
| `sensor.einspeisung_gesamt` | Einspeisung ins Netz (kWh) |
| `sensor.solar_eigenverbrauch` | Solar selbst verbraucht (nicht eingespeist) |
| `sensor.batterie_eigenverbrauch` | Netto-Batterieentnahme (kWh) |
| `sensor.eingespart_gesamt` | Gesamt eingespart (Solar + Batterie) |

---

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
3. Die Platzhalter durch eigene Entity-IDs ersetzen:

```yaml
sensor.PHASE_A          → z.B. sensor.shellyem3_channel_a_energy
sensor.PHASE_B          → z.B. sensor.shellyem3_channel_b_energy
sensor.PHASE_C          → z.B. sensor.shellyem3_channel_c_energy
sensor.SOLAR_PRODUKTION → z.B. sensor.hoymiles_hm_600_total_production
sensor.BATTERIE_LADEN   → z.B. sensor.victron_battery_charged_energy
sensor.BATTERIE_ENTLADEN→ z.B. sensor.victron_battery_discharged_energy
```

4. In `configuration.yaml` eintragen (falls noch nicht vorhanden):
```yaml
homeassistant:
  packages: !include_dir_named packages
```

5. HA neu starten

### Schritt 4 – Automation anlegen

1. **Einstellungen → Automatisierungen → Blueprint-Automation erstellen**
2. "Virtueller Stromzähler (3-Phasen + Solar + Batterie)" auswählen
3. Alle Sensoren und Helfer aus den Dropdowns auswählen
4. Speichern

### Schritt 5 – Zählerstand eintragen

Den aktuellen Zählerstand in den Helper **"Zählerstand Basis"** eintragen.
Der Offset wird automatisch gesetzt und der Zähler läuft ab sofort weiter.

---

## Energiefluss-Logik

```
Bezug        = Phasen L1+L2+L3 (nur positive Werte → vom Netz)
Einspeisung  = Phasen L1+L2+L3 (nur negative Werte → ins Netz, als positiv)
Eigenverbrauch Solar = Hoymiles Produktion − Einspeisung
Eingespart   = Eigenverbrauch Solar + Victron Entladung
```

> **Hinweis Shelly 3EM:** Negative Phasenwerte bei Einspeisung werden korrekt
> erkannt und separat ausgewiesen. Der Bezug-Zähler verfälscht sich nicht.

---

## Dashboard-Karte

Den Inhalt von [`lovelace/card.yaml`](lovelace/card.yaml) im Lovelace-Editor
als manuelle Karte einfügen.
