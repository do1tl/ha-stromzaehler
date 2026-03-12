# ha-stromzaehler

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.1+-blue.svg)](https://www.home-assistant.io/)

Vollständige Energiebilanz als **Custom Integration** für Home Assistant.
Kein YAML anfassen – alles über die UI einrichten.

**Kompatibel mit:**
- Shelly 3EM (und allen anderen 3-Phasen-Energiezählern)
- Hoymiles, SMA, Fronius, Enphase (und jeder anderen Solaranlage)
- Victron, SolarEdge, BYD (und jedem anderen Batteriespeicher)

## Automatisch erstellte Sensoren

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.zahlerstand_aktuell` | Aktueller Zählerstand in kWh |
| `sensor.jahresverbrauch_bezug` | Bezug vom Netz seit letzter Eingabe |
| `sensor.einspeisung_gesamt` | Einspeisung ins Netz (kWh) |
| `sensor.solar_eigenverbrauch` | Solar selbst verbraucht (nicht eingespeist) |
| `sensor.batterie_eigenverbrauch` | Netto-Batterieentnahme (kWh) |
| `sensor.eingespart_gesamt` | Gesamt eingespart (Solar + Batterie) |

---

## Installation via HACS

1. HACS öffnen → **Integrationen** → Drei-Punkte-Menü → **Benutzerdefinierte Repositories**
2. URL eintragen: `https://github.com/do1tl/ha-stromzaehler`
3. Kategorie: **Integration**
4. **Hinzufügen** klicken
5. Integration "Virtueller Stromzähler" suchen und installieren
6. Home Assistant neu starten

## Einrichten

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. "Virtueller Stromzähler" suchen
3. **Schritt 1:** 3 Phasen-Sensoren auswählen + aktuellen Zählerstand eintragen
4. **Schritt 2:** Solar-Sensor auswählen (optional, überspringen möglich)
5. **Schritt 3:** Batterie Lade/Entlade-Sensoren auswählen (optional)
6. Fertig – alle Sensoren werden automatisch angelegt

## Zählerstand aktualisieren (jährlich)

**Option 1 – UI:**
Einstellungen → Geräte & Dienste → Virtueller Stromzähler → **Konfigurieren** → neuen Wert eintragen

**Option 2 – Service:**
```yaml
service: stromzaehler.set_meter_reading
data:
  value: 12345
```

**Option 3 – Automation (z.B. jedes Jahr am 1. Januar):**
```yaml
automation:
  trigger:
    - platform: time
      at: "00:00:00"
  condition:
    - condition: template
      value_template: "{{ now().month == 1 and now().day == 1 }}"
  action:
    - service: stromzaehler.set_meter_reading
      data:
        value: "{{ states('input_number.mein_zaehlerstand') | float }}"
```

---

## Energiefluss-Logik

```
Bezug           = Phasen L1+L2+L3 (nur positive Werte → vom Netz)
Einspeisung     = Phasen L1+L2+L3 (nur negative Werte → ins Netz, als positiv)
Solar-EV        = Hoymiles Produktion − Einspeisung
Batterie-EV     = Victron Entladung − Victron Ladung
Eingespart      = Solar-EV + Batterie-EV
Zählerstand     = Eingegebener Startwert + Bezug seit Eingabe
```

> **Shelly 3EM:** Negative Phasenwerte bei Einspeisung werden automatisch korrekt erkannt.
> Der Bezug-Zähler verfälscht sich nicht.

---

## Dashboard-Karte

Inhalt von [`lovelace/card.yaml`](lovelace/card.yaml) im Lovelace-Editor als manuelle Karte einfügen.
