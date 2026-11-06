# Anforderungsspezifikation – Template Attributes (HA Helper)

Dieses Dokument fasst alle fachlichen und technischen Anforderungen an das Projekt
`ha-template-attributes` zusammen. Es dient als Referenz, um das Projekt bei Bedarf komplett
neu aufzusetzen, und wird fortlaufend gepflegt.

Der Bereich **Funktionale Anforderungen** beschreibt, *was* die Integration können muss,
unabhängig von der technischen Umsetzung. Der Bereich **Technische Aspekte** beschreibt die
*konkrete* Umsetzung und kann beim Neuaufbau ersetzt werden.

> **Pflegehinweis:** Bei neuen oder geänderten Anforderungen wird dieses Dokument im selben
> Change aktualisiert. Erledigt = „im aktuellen Code umgesetzt“, nicht „irgendwann gewünscht“.

---

## 1. Zweck des Projekts

Eine Home-Assistant-Integration (HACS), mit der sich ein **Template-Sensor mit beliebig vielen
zusätzlichen Attributen** komplett in der HA-Oberfläche anlegen und pflegen lässt – ohne YAML.
Wie beim Schwesterprojekt `ha-template-forecast` wird ein Standard-Sensor nachgebildet
(Zustand per Template, Einheit, Geräte-/Statusklasse, Icon); zusätzlich können eigene Attribute
mit je **eigenem Template** hinzugefügt und wieder gelöscht werden.

## 2. Funktionale Anforderungen

### 2.1 Standard-Sensor

- **F-1** Über „Helfer erstellen“ wird ein Sensor mit Name und **State-Template** angelegt.
- **F-2** Optional: Einheit, Geräteklasse, Statusklasse, Icon, Neuberechnungsintervall
  (Standard 15 Minuten, mindestens 1).
- **F-3** Diese Einstellungen sind nachträglich über „Optionen“ des Helfers änderbar; die
  Änderung wirkt ohne Neustart von HA.
- **F-4** Ein Template mit Syntaxfehler oder einem Fehler beim Testrendern wird mit lokalisierter
  Fehlermeldung am betroffenen Feld abgelehnt (inkl. der Fehlermeldung von Jinja).

### 2.2 Eigene Attribute

- **F-5** Ein Helfer hat eine geordnete Liste beliebig vieler Attribute; jedes besteht aus
  **Name** und **eigenem Template**.
- **F-6** Hinzufügen: **unter dem letzten Abschnitt** steht ein Eingabefeld für den Namen mit
  Button „Attribut hinzufügen“ (auch Enter). Es entsteht ein neuer, **geöffneter** Abschnitt zur
  Bearbeitung des Templates; darunter steht wieder das Eingabefeld für das nächste Attribut.
- **F-7** Löschen: **hinter jedem Attributnamen** ein kleines Papierkorb-Symbol; es entfernt das
  Attribut samt Template. Das Löschen wird erst mit „Speichern“ wirksam.
- **F-8** Namensregeln: nicht leer, nur Buchstaben/Ziffern/Unterstrich, nicht mit Ziffer
  beginnend, eindeutig innerhalb des Helfers, kein von HA reservierter Name
  (z. B. `friendly_name`, `icon`, `unit_of_measurement`, `device_class`, `state_class`, …).
  Verstöße werden sofort (beim Hinzufügen) bzw. beim Speichern lokalisiert gemeldet.
- **F-9** Im Template eines Attributs steht die Variable `state` (aktueller Zustand des Sensors)
  zur Verfügung. Das Ergebnis behält seinen Typ (Zahl, Liste, Objekt, Text).

### 2.3 Darstellung / Bedienung

- **F-10** Name und Template gehören zusammen: je Attribut **ein Abschnitt** (aufklappbar), im
  Titel stehen **Name und aktueller Wert** („Name = Wert“, lange Werte werden gekürzt).
  Dasselbe gilt für den Standard-Sensor („Zustand = Wert“).
- **F-11** **Alle Abschnitte sind zunächst geschlossen**, damit Attribute und Werte auf einen
  Blick sichtbar sind. Geöffnet sind nur der gerade neu hinzugefügte Abschnitt und Abschnitte
  mit einem Validierungsfehler. Nach dem Speichern sind wieder alle geschlossen.
- **F-12** Der Wert im Titel folgt dem tatsächlichen Zustand der Entität (live, ohne Neuladen).
- **F-13** Änderungen werden gesammelt und mit „Speichern“ übernommen (validiert als Ganzes);
  „Änderungen verwerfen“ setzt zurück. Bei Validierungsfehlern wird nichts gespeichert und der
  Fehler am betroffenen Abschnitt angezeigt.
- **F-14** Die Oberfläche ist deutsch und englisch (nach HA-Sprache).
- **F-15** Gibt es mehrere Helfer, kann der zu bearbeitende gewählt werden; es gibt einen Link zu
  den Einstellungen des Standard-Sensors (F-3).
- **F-20** Die „Optionen“ des Helfers enthalten einen Link „Attribute verwalten“, der direkt das
  Panel mit **diesem** Helfer öffnet (nicht nur den ersten). Ob das Panel in der Seitenleiste
  erscheint, verwaltet jeder Nutzer selbst über die HA-Seitenleisten-Einstellungen; es gibt dafür
  keine eigene Option der Integration.

### 2.4 Verhalten des Sensors

- **F-16** Zustand und Attribute werden neu berechnet, wenn sich eine Entität ändert, die ein
  Template liest, sowie periodisch (F-2).
- **F-17** Ein fehlerhaftes Template zur Laufzeit wird geloggt; der **letzte gute Wert bleibt**,
  andere Attribute sind nicht betroffen, HA läuft ungestört weiter.
- **F-18** Nach einem Neustart wird der letzte Zustand wiederhergestellt (nur noch definierte
  Attribute).
- **F-19** Änderungen an Template/Attributen wirken sofort (Entität wird neu geladen).

## 3. Nicht-funktionale Anforderungen

- Keine YAML-Konfiguration nötig – vollständige Bedienung über die HA-UI.
- Robustheit: Fehler in Nutzereingaben/-templates destabilisieren Home Assistant nie.
- Lokalisierte, feldgenaue Fehlermeldungen.
- Testbarkeit ohne reale HA-Instanz plus UI-Absicherung im echten Browser.
- Automatisiertes Releasing (Conventional Commits, semantic-release) mit Test-Gate.
- Dokumentation (README, Beispiele) zweisprachig; diese Spezifikation nur deutsch.

## 4. Technische Aspekte (Umsetzung, ersetzbar)

### 4.1 Plattform & Aufbau

- Custom Integration `template_attributes`, `integration_type: helper`, `iot_class: calculated`,
  Config Entry pro Helfer. Wirksame Konfiguration = `data` gemischt mit `options` (`options`
  gewinnt). Attribute liegen als Liste `attributes: [{name, template}]` im Entry.
- **Config-/Options-Flow** (`config_flow.py`) deckt nur den Standard-Sensor ab (F-1…F-4). Ein
  Config-Flow kann weder Live-Werte in Abschnittstiteln noch Hinzufügen-/Löschen-Buttons
  darstellen – deshalb übernimmt die Attribute ein eigenes Panel. Der Options-Flow übernimmt
  `options` per Merge, damit `attributes` erhalten bleiben.
- **Validierung** (`validation.py`) ist die gemeinsame Quelle für Flow und Websocket: Syntaxcheck
  (`Template.ensure_valid`) plus ein Testrender (`state` = 0 für Attribute).
- **Sensor** (`sensor.py`): `SensorEntity` + `RestoreEntity`; Abhängigkeiten über
  `async_render_to_info`, `async_track_state_change_event`, `async_track_time_interval`.
  Fehler pro Template werden einzeln abgefangen (F-17). Neuladen bei Änderung der Entry über
  einen Update-Listener (`__init__.py`).
- **Websocket-API** (`websocket_api.py`, nur Admin): `template_attributes/list` und
  `template_attributes/save`. Validierungsfehler sind ein normales Ergebnis
  (`{ok: false, errors: {state_template?, attributes?: {name: {code, message}}}}`), kein
  Websocket-Fehler. Speichern schreibt nur `state_template` und `attributes` in die `options`.
- **Panel** (`frontend.py`, `www/template-attributes-panel.js`): Sidebar-Panel über
  `panel_custom`, Vanilla-JS-Custom-Element mit Shadow DOM, kein Build-Schritt. Der Wert im
  Abschnittstitel wird aus `hass.states[entity_id]` gelesen (F-12). Texte DE/EN im Skript.
  Registrierung schlägt nie auf die Integration durch. Deep-Link (F-20): `/template-attributes?entry=<entry_id>`;
  das Panel liest den Parameter beim Start und fällt bei unbekannter ID auf den ersten Helfer zurück.
  Der Options-Flow liefert die URL als Platzhalter `panel_url` an die Beschreibung.
- Übersetzungen: `strings.json` = `translations/en.json`, `translations/de.json`
  schlüsselgleich (ICU MessageFormat).

### 4.2 Tests

- `tests/` (`python -m pytest`): gemockte HA-Instanz – Flow, Sensor, Websocket-API, Übersetzungen.
- `tests_e2e/` (`python -m pytest tests_e2e`): echte `hass`-Instanz + echtes Frontend +
  Playwright (Chromium); legt einen Helfer über die Flow-API an und prüft das Panel
  (F-6, F-7, F-10, F-11, F-13, F-20). Screenshots in `tests_e2e/screenshots/` nach jedem Lauf ansehen.
- Beides läuft im Devcontainer (`.devcontainer/`).

### 4.3 CI/CD

- GitHub Actions: `test.yml` (PR), `test-e2e.yml` (PR, kein Gate), `release.yml`
  (semantic-release, Job `release` wartet auf `test`). Conventional Commits.
  `scripts/bump_version.py` schreibt die Version in `manifest.json`.

## 5. Offene Punkte / Ideen

- Live-Vorschau des Werts schon während der Bearbeitung (Testrender vor dem Speichern).
- Template-Editor mit Syntax-Highlighting (`ha-code-editor`) statt Textarea.
- Anlegen eines neuen Helfers direkt im Panel.
