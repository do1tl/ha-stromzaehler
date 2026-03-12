# ha-stromzaehler

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2023.1+-blue.svg)](https://www.home-assistant.io/)

Vollständige Energiebilanz als **Custom Integration** für Home Assistant.
Kein YAML anfassen – alles über die UI einrichten.

**Kompatibel mit:**
- Shelly 3EM (und allen anderen 3-Phasen-Energiezählern)
- Hoymiles, SMA, Fronius, Enphase (und jeder anderen Solaranlage)
- JBD BMS, Victron, SolarEdge, BYD (und jedem anderen Batteriespeicher)

---

## Installation via HACS

1. HACS öffnen → **Integrationen** → Drei-Punkte-Menü → **Benutzerdefinierte Repositories**
2. URL eintragen: `https://github.com/do1tl/ha-stromzaehler`
3. Kategorie: **Integration**
4. **Hinzufügen** klicken
5. Integration „Virtueller Stromzähler" suchen und installieren
6. Home Assistant **neu starten**

---

## Einrichten – Schritt für Schritt

### Schritt 1 – Phasen & Zählerstand

Wähle die 3 Energie-Sensoren deines Stromzählers (Bezug vom Netz).

| Feld | Beispiel Shelly 3EM |
|------|---------------------|
| Phase L1 – Bezug | `sensor.shellyem3_xxxxxx_channel_a_energy` |
| Phase L2 – Bezug | `sensor.shellyem3_xxxxxx_channel_b_energy` |
| Phase L3 – Bezug | `sensor.shellyem3_xxxxxx_channel_c_energy` |
| Aktueller Zählerstand | Wert vom physischen Hauszähler ablesen und eintragen (z.B. `1400`) |

> Der Zählerstand-Wert entspricht dem, was aktuell auf deinem Stromzähler steht.
> Ab diesem Moment zählt die Integration alle neu verbrauchten kWh dazu.

---

### Schritt 2 – Einspeisung (optional)

Nur ausfüllen wenn dein Stromzähler **getrennte Einspeise-Sensoren** hat.

| Feld | Beispiel Shelly 3EM |
|------|---------------------|
| Phase L1 – Einspeisung | `sensor.shellyem3_xxxxxx_channel_a_energy_returned` |
| Phase L2 – Einspeisung | `sensor.shellyem3_xxxxxx_channel_b_energy_returned` |
| Phase L3 – Einspeisung | `sensor.shellyem3_xxxxxx_channel_c_energy_returned` |

> **Leer lassen** wenn dein Sensor negative Werte bei Einspeisung liefert – das wird automatisch erkannt.

---

### Schritt 3 – Solaranlage (optional)

Wähle den **Gesamtertrag-Sensor** deiner Solaranlage oder deines Wechselrichters.

| Gerätetyp | Sensor |
|-----------|--------|
| Hoymiles HM-400 | `sensor.hoymiles_hm_400_yieldtotal` |
| Hoymiles (Kanal) | `sensor.hoymiles_hm_400_ch1_yieldtotal` |
| SMA Wechselrichter | `sensor.sma_total_yield` |
| Fronius | `sensor.fronius_total_energy` |

> Wichtig: **YieldTotal** (Gesamtertrag) verwenden, nicht YieldDay (Tagesertrag – resettet täglich).

> **Leer lassen** falls keine Solaranlage vorhanden.

---

### Schritt 4 – Batteriespeicher (optional)

Zwei Varianten – nur eine davon ausfüllen:

#### Variante A – Netto-Sensor (z.B. JBD BMS)
Für Sensoren die **positive Werte beim Laden** und **negative Werte beim Entladen** liefern.
Mehrere Akkus möglich – alle auswählen, sie werden automatisch summiert.
Wh wird automatisch in kWh umgerechnet.

| Feld | Beispiel JBD BMS |
|------|-----------------|
| A) Batterie Netto-Energie | `sensor.mh12v100_00548_leistung` + `sensor.mh12v100_00557_leistung` |

> Hinweis: Leistungs-Sensoren (W) müssen zuerst über einen **Integral-Helfer** (Riemann-Summe) in Energie (kWh) umgewandelt werden.
> Einstellungen → Helfer → Erstellen → Integral-Sensor → Quelle: Leistungs-Sensor → Methode: Trapezoid

#### Variante B – Separate Sensoren (z.B. Victron BMV, Shelly)

| Feld | Beispiel |
|------|---------|
| B) Batterie Lade-Energie | `sensor.victron_battery_charged_energy` |
| B) Batterie Entlade-Energie | `sensor.victron_battery_discharged_energy` |

> **Alles leer lassen** falls kein Batteriespeicher vorhanden.

---

## Automatisch erstellte Sensoren

| Sensor | Beschreibung |
|--------|-------------|
| `sensor.zahlerstand_aktuell` | Aktueller Zählerstand in kWh (Startwert + Bezug seit Setup) |
| `sensor.jahresverbrauch_bezug` | Bezug vom Netz seit letztem Zählerstand-Update |
| `sensor.einspeisung_gesamt` | Gesamte Einspeisung ins Netz (kWh) |
| `sensor.solar_eigenverbrauch` | Solar selbst verbraucht (Produktion − Einspeisung) |
| `sensor.batterie_eigenverbrauch` | Netto-Batterieentnahme (Entladung − Ladung) |
| `sensor.eingespart_gesamt` | Gesamt eingespart (Solar-EV + Batterie-EV) |
| `sensor.phasen_gesamt_bezug` | Rohsumme aller Phasen (kWh, Bezug) |

---

## Zählerstand aktualisieren (jährlich)

Wenn der Stromableser kommt, trägst du den neuen Wert ein – der interne Referenzpunkt wird automatisch neu gesetzt.

**Option 1 – UI:**
Einstellungen → Geräte & Dienste → Virtueller Stromzähler → **Konfigurieren** → neuen Wert eintragen

**Option 2 – Automation (z.B. jedes Jahr am 1. Januar):**
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
        value: 12345  # aktuellen Zählerstand eintragen
```

---

## Dashboard einrichten

### Variante A – Einzelne Karte einfügen

1. Dashboard öffnen → **Bearbeiten** (Stift-Icon oben rechts)
2. **Karte hinzufügen** → ganz nach unten scrollen → **Manuell**
3. Inhalt von [`lovelace/card.yaml`](lovelace/card.yaml) einfügen
4. **Speichern**

### Variante B – Eigenes Dashboard erstellen

1. **Einstellungen → Dashboards → Dashboard hinzufügen**
2. Titel vergeben (z.B. „Stromzähler"), Typ: **Standard**
3. Dashboard öffnen → **Bearbeiten** → Drei-Punkte-Menü → **Raw-Konfigurationseditor**
4. Inhalt von [`lovelace/dashboard.yaml`](lovelace/dashboard.yaml) einfügen
5. **Speichern**

### Welche Sensoren werden in den Karten verwendet?

Die Karten verwenden automatisch die Sensoren die die Integration anlegt:

| Anzeige | Sensor |
|---------|--------|
| Zählerstand | `sensor.zahlerstand_aktuell` |
| Jahresverbrauch | `sensor.jahresverbrauch_bezug` |
| Einspeisung | `sensor.einspeisung_gesamt` |
| Solar Eigenverbrauch | `sensor.solar_eigenverbrauch` |
| Batterie Eigenverbrauch | `sensor.batterie_eigenverbrauch` |
| Eingespart | `sensor.eingespart_gesamt` |

> Falls die Sensoren einen anderen Namen haben (z.B. bei mehreren Instanzen), müssen die Entity-IDs in der Karte angepasst werden.

---

## Energiefluss-Logik

```
Bezug        = Summe L1+L2+L3 (nur positive Werte = vom Netz)
Einspeisung  = Summe energy_returned L1+L2+L3 (oder negative Phasenwerte)
Solar-EV     = Solar Gesamtertrag − Einspeisung
Batterie-EV  = Entladung − Ladung
Eingespart   = Solar-EV + Batterie-EV
Zählerstand  = Eingetragener Startwert + Bezug seit Setup
```
