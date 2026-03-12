# CHANGELOG & IDEEN – Virtueller Stromzähler

Stand: März 2026

---

## Bekannte Probleme / Bugs

### Batterie-Tracking ohne Energiesensor
**Problem:** JBD BMS (`mh12v100_00548/00557`) liefert nur Leistungs-Sensoren (W), keine Energiesensoren (kWh).
Victron MPPT hat nur Tagesertrag (resettet täglich) → kein akkumulierter Gesamtertrag.
**Workaround:** Riemann-Sum-Helper in HA manuell anlegen (W → kWh).
**Idee:** Riemann-Sum direkt in die Integration einbauen – Leistungs-Sensor auswählen, Integration rechnet intern.

### Solar vs. Batterie-Wechselrichter unklar
**Problem:** Hoymiles HM-400 ist an der Batterie angeschlossen (kein direkter Solar-Eingang).
Dadurch ist Hoymiles YieldTotal = Batterie-Entladung, nicht Solar-Produktion.
Victron MPPT = Solar → Batterie (Ladung), kein guter Gesamt-Ertragssensor.
**Idee:** Setup-Assistent besser erklären welcher Sensor wohin gehört, ggf. Gerätekategorie auswählbar machen.

---

## Geplante Verbesserungen

### Integration

- [ ] **Leistungs-Sensoren (W) direkt unterstützen**
  Integration integriert intern (Riemann-Sum) → kein separater Helper nötig
  Betrifft: JBD BMS `leistung`, Victron `pv_leistung`, Shelly `power`

- [ ] **Victron MPPT Gesamt-Ertrag**
  Aktuell nur Tagesertrag verfügbar. Idee: eigenen akkumulierenden Sensor
  aus Tagesertrag bauen (täglich aufaddieren via Automation oder intern).

- [ ] **HA Energie-Dashboard Integration**
  Sensoren so konfigurieren dass sie im offiziellen HA Energie-Dashboard
  (`sensor.state_class = total_increasing`) korrekt angezeigt werden.
  Prüfen ob alle Sensoren dafür geeignet sind.

- [ ] **Mehrere Solar-Quellen**
  Aktuell nur ein Solar-Sensor. Idee: Mehrfachauswahl wie bei Batterie.
  Nützlich wenn z.B. Hoymiles + Victron beide Solar liefern.

- [ ] **Reset-Option für Jahresverbrauch**
  Automatischer Reset am 1. Januar via eingebautem Automations-Trigger
  ohne dass der Nutzer manuell den Zählerstand eintippen muss.

- [ ] **Echtzeit-Leistungsanzeige (W)**
  Zusätzliche Sensoren für aktuelle Leistung (nicht nur kWh gesamt):
  - Aktuelle Bezugsleistung (W)
  - Aktuelle Einspeiseleistung (W)
  - Aktuelle Solar-Leistung (W)

- [ ] **Konfigurations-Update ohne Neuanlage**
  Aktuell muss die Integration gelöscht und neu eingerichtet werden
  wenn z.B. ein Batterie-Sensor nachträglich hinzugefügt werden soll.
  Idee: Options-Flow erweitern um alle Sensoren nachträglich änderbar zu machen.

- [ ] **Validierung im Setup**
  Prüfen ob ausgewählte Sensoren gültige Werte liefern bevor gespeichert wird.
  Fehlermeldung wenn Sensor `unavailable` oder falsche Einheit hat.

### Dashboard / Karten

- [ ] **Tages-/Wochen-/Monatsansicht umschaltbar**
  Statistik-Graph mit Buttons zum Umschalten des Zeitraums.

- [ ] **Kostenberechnung**
  Eingabe Strompreis (ct/kWh) → Integration berechnet Kosten und Ersparnis in €.
  Sensor: `sensor.stromkosten_monat`, `sensor.ersparnis_monat`

- [ ] **Gauge-Karte für Eigenverbrauchsquote**
  Prozent selbst verbrauchter Solar-Strom visuell als Tacho darstellen.
  `Solar-EV / Solar-Gesamt * 100`

- [ ] **Vergleich Vorjahr**
  Wenn genug Historik vorhanden: Vergleich aktueller Monat vs. Vorjahr.

---

## Aktuelle Sensor-Konfiguration (unser Setup)

| Schritt | Sensor | Gerät |
|---------|--------|-------|
| Phase L1 Bezug | `sensor.shellyem3_485519d9e23e_channel_a_energy` | Shelly 3EM |
| Phase L2 Bezug | `sensor.shellyem3_485519d9e23e_channel_b_energy` | Shelly 3EM |
| Phase L3 Bezug | `sensor.shellyem3_485519d9e23e_channel_c_energy` | Shelly 3EM |
| Phase L1 Einspeisung | `sensor.shellyem3_485519d9e23e_channel_a_energy_returned` | Shelly 3EM |
| Phase L2 Einspeisung | `sensor.shellyem3_485519d9e23e_channel_b_energy_returned` | Shelly 3EM |
| Phase L3 Einspeisung | `sensor.shellyem3_485519d9e23e_channel_c_energy_returned` | Shelly 3EM |
| Solar | `sensor.hoymiles_hm_400_yieldtotal` | Hoymiles HM-400 (an Batterie) |
| Batterie | nicht konfiguriert | JBD BMS hat nur W-Sensoren |

**Verfügbare Sensoren die noch nicht genutzt werden:**
- `sensor.mh12v100_00548_leistung` – Batterie 1 Leistung (W, +Laden/−Entladen)
- `sensor.mh12v100_00557_leistung` – Batterie 2 Leistung (W, +Laden/−Entladen)
- `sensor.smartsolar_hq2412f3reh_pv_leistung` – Victron PV Leistung (W)
- `sensor.smartsolar_hq2412f3reh_heutiger_ertrag` – Victron Tagesertrag (kWh, resettet täglich)
- `sensor.pv_power`, `sensor.pv_voltage`, `sensor.pv_current` – PV-Daten

---

## Versions-Historie

| Version | Änderung |
|---------|----------|
| 1.0.0 | Erste Version – Phasen, Solar, Batterie (ein Sensor je) |
| 1.1.0 | Mehrfachauswahl für Batterie-Sensoren (Multi-BMS) |
| 1.2.0 | JBD BMS Netto-Sensor (+/−), Wh→kWh Umrechnung |
| 1.3.0 | Separate Einspeisung-Sensoren (Shelly energy_returned), neuer Setup-Schritt |
| 1.3.1 | Bugfix: Phasen-Offset beim Setup korrekt setzen |
