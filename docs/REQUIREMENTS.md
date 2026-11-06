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
zusätzlichen Attributen** komplett in den Standard-Dialogen der HA-Oberfläche anlegen und pflegen
lässt – ohne YAML und ohne eigenes Panel. Wie beim Schwesterprojekt `ha-template-forecast` wird ein
Standard-Sensor nachgebildet (Zustand per Template, Einheit, Geräte-/Statusklasse, Icon); zusätzlich
können eigene Attribute mit je **eigenem Template** hinzugefügt, umbenannt und gelöscht werden.

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
- **F-6** Hinzufügen beim **Erstellen**: Nach dem Standard-Sensor folgt ein Schritt „Attribut
  hinzufügen“ (Name, Template, Haken „Weiteres Attribut hinzufügen“). Mit Haken wird das Attribut
  übernommen und sofort eine neue, leere Eingabe geöffnet; ohne Haken wird der Helfer angelegt.
  Bleibt der Name leer, ist der Schritt übersprungen bzw. beendet.
- **F-7** Bearbeiten in den **Optionen**: Jedes vorhandene Attribut ist ein **eingeklappter
  Abschnitt**, dessen **Titel der Attributname** ist. Darin: Name, Template (Standard-Template-
  Editor) und ein **Schalter „Dieses Attribut löschen“** (als erstes Feld des Abschnitts, mit dem
  Hinweis, dass Name und Template dann ignoriert werden). Ein geänderter Name **benennt** das
  Attribut um. Ein Formular kann Felder nicht live deaktivieren oder einfärben; deshalb gibt es vor
  dem Speichern einen **Bestätigungsschritt** (F-19).
- **F-19** Werden beim Absenden der Optionen Attribute gelöscht oder umbenannt, zeigt ein
  Bestätigungsschritt, was gelöscht und was umbenannt wird („Gelöscht: …“, „Umbenannt: alt → neu“).
  Erst „Absenden“ übernimmt die Änderungen; ein Haken „Zurück und weiter bearbeiten“ führt zum
  Formular mit den bisherigen Eingaben zurück. Ohne Löschen/Umbenennen entfällt der Schritt.
- **F-8** Namensregeln: nicht leer, nur Buchstaben/Ziffern/Unterstrich, nicht mit Ziffer
  beginnend, eindeutig innerhalb des Helfers, kein von HA reservierter Name
  (z. B. `friendly_name`, `icon`, `unit_of_measurement`, `device_class`, `state_class`, …) und kein
  Feldname des Formulars (`state_template`, `update_interval_minutes`, `add_attribute`).
  Verstöße werden mit lokalisierter Meldung (inkl. Attributname) angezeigt, es wird nichts gespeichert.
- **F-9** Im Template eines Attributs steht die Variable `state` (aktueller Zustand des Sensors)
  zur Verfügung. Das Ergebnis behält seinen Typ (Zahl, Liste, Objekt, Text).
- **F-10** Templates (State und Attribute) werden mit dem **Standard-Template-Editor von Home
  Assistant** bearbeitet (Syntax-Hervorhebung, Autovervollständigung).
- **F-11** Unter den Abschnitten der vorhandenen Attribute steht ein **Haken „Nach dem Speichern
  ein neues Attribut hinzufügen“**. Ist er gesetzt, öffnet sich nach dem Absenden der Schritt
  „Attribut hinzufügen“ (wie F-6, mit „Weiteres Attribut hinzufügen“); gespeichert wird erst am Ende.
- **F-12** Bei Validierungsfehlern wird nichts gespeichert; das Formular bleibt offen und behält
  die Eingaben (inkl. Umbenennungen und gesetzter Lösch-Schalter).
- **F-13** Ein zum Löschen markiertes Attribut wird nicht mehr validiert.
- **F-14** Die Oberfläche ist deutsch und englisch (nach HA-Sprache).

### 2.3 Verhalten des Sensors

- **F-15** Zustand und Attribute werden neu berechnet, wenn sich eine Entität ändert, die ein
  Template liest, sowie periodisch (F-2).
- **F-16** Ein fehlerhaftes Template zur Laufzeit wird geloggt; der **letzte gute Wert bleibt**,
  andere Attribute sind nicht betroffen, HA läuft ungestört weiter.
- **F-17** Nach einem Neustart wird der letzte Zustand wiederhergestellt (nur noch definierte
  Attribute; ein umbenanntes oder gelöschtes Attribut verschwindet).
- **F-18** Änderungen an Template/Attributen wirken sofort (Entität wird neu geladen).

## 3. Nicht-funktionale Anforderungen

- Keine YAML-Konfiguration nötig – vollständige Bedienung über die HA-UI.
- Keine eigene Frontend-Komponente (Panel, JS): nur Standard-Dialoge von Home Assistant.
- Robustheit: Fehler in Nutzereingaben/-templates destabilisieren Home Assistant nie.
- Lokalisierte Fehlermeldungen mit Bezug zum Attribut.
- Testbarkeit ohne reale HA-Instanz plus UI-Absicherung im echten Browser.
- Automatisiertes Releasing (Conventional Commits, semantic-release) mit Test-Gate.
- Dokumentation (README, Beispiele) zweisprachig; diese Spezifikation nur deutsch.

## 4. Technische Aspekte (Umsetzung, ersetzbar)

### 4.1 Plattform & Aufbau

- Custom Integration `template_attributes`, `integration_type: helper`, `iot_class: calculated`,
  Config Entry pro Helfer. Wirksame Konfiguration = `data` gemischt mit `options` (`options`
  gewinnt). Attribute liegen als Liste `attributes: [{name, template}]` im Entry.
- **Config-Flow** (`config_flow.py`): Schritt `user` (Standard-Sensor) → Schritt `attribute`
  (wiederholt, solange `add_another` gesetzt ist) → Entry. Der Entry wird erst am Ende angelegt.
- **Options-Flow**: Schritt `init` = Standard-Sensor-Felder + je Attribut ein
  `data_entry_flow.section` (eingeklappt) + Boolean `add_attribute`; danach optional derselbe
  Schritt `attribute`. Zwischen `init` und dem Rest liegt bei Löschungen/Umbenennungen der Schritt
  `confirm` (Platzhalter `changes`, Haken `go_back`). Gespeichert wird einmal am Ende (`async_create_entry` mit allen Optionen).
  `options` werden per Merge übernommen, damit unbekannte Schlüssel erhalten bleiben.
- **Abschnitte**: Der Schlüssel eines Abschnitts ist der *ursprüngliche* Attributname; HA zeigt ihn
  als Titel, weil es keine Übersetzung dafür gibt. Weil die Schlüssel dynamisch sind, können die
  Feldlabels im Abschnitt („Name“, „Template“, „Dieses Attribut löschen“) nicht aus den
  Übersetzungsdateien kommen; sie stehen in `SECTION_LABELS` (`config_flow.py`) und werden nach der
  HA-Serversprache gewählt. Der Lösch-Schalter ist ein `BooleanSelector` (rendert als Schalter, ein
  einfaches `bool` wäre ein Kontrollkästchen). Wegen des Abschnittsschlüssels dürfen Attributnamen
  nicht wie Formularfelder heißen (F-8, `RESERVED_ATTRIBUTE_NAMES`).
- **Fehler** der Attribute sind `base`-Fehler mit den Platzhaltern `attribute` und
  `template_error` (Fehler in Abschnittsfeldern lassen sich im Formular nicht feldgenau anzeigen).
  Das State-Template behält seinen feldgenauen Fehler.
- **Validierung** (`validation.py`): Syntaxcheck (`Template.ensure_valid`) plus ein Testrender
  (`state` = 0 für Attribute); Namensregeln in `check_attribute_names`, gesamte Attributliste in
  `check_attributes`.
- **Sensor** (`sensor.py`): `SensorEntity` + `RestoreEntity`; Abhängigkeiten über
  `async_render_to_info`, `async_track_state_change_event`, `async_track_time_interval`.
  Fehler pro Template werden einzeln abgefangen (F-16). Neuladen bei Änderung des Entry über
  einen Update-Listener (`__init__.py`).
- Übersetzungen: `strings.json` = `translations/en.json`, `translations/de.json`
  schlüsselgleich (ICU MessageFormat; kein einfacher Apostroph in Texten mit Platzhaltern).

### 4.2 Tests

- `tests/` (`python -m pytest`): gemockte HA-Instanz – Flow (Erstellen, Attribut-Schritt, Abschnitte,
  Umbenennen, Löschen, Fehler), Sensor, Übersetzungen.
- `tests_e2e/` (`python -m pytest tests_e2e`): echte `hass`-Instanz + echtes Frontend +
  Playwright (Chromium); legt einen Helfer über die Flow-API an und klickt den Options-Dialog durch
  (Abschnitte, Umbenennen, Löschen, Haken „Neues Attribut“). Screenshots in `tests_e2e/screenshots/`
  nach jedem Lauf ansehen.
- Beides läuft im Devcontainer (`.devcontainer/`).

### 4.3 CI/CD

- GitHub Actions: `test.yml` (PR), `test-e2e.yml` (PR, kein Gate), `release.yml`
  (semantic-release, Job `release` wartet auf `test`). Conventional Commits.
  `scripts/bump_version.py` schreibt die Version in `manifest.json`.

## 5. Offene Punkte / Ideen

- Live-Wert der Attribute im Dialog (nicht möglich: Formulare kennen keine Live-Werte).
- Reihenfolge der Attribute ändern.
- Eigene Seitenleisten-Ansicht (früher als Panel vorhanden, entfernt, siehe Abschnitt 1).
