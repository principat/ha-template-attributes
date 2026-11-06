# Template Attributes (Home Assistant Helper)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=principat&repository=ha-template-attributes&category=integration)

**English** | [Deutsche Version](#deutsch) (further down in this file)

A HACS custom integration for a template sensor with **any number of extra attributes**, each with
its own Jinja2 template - entirely through the Home Assistant UI, no YAML.

> [!WARNING]
> **Alpha:** This project is still in an early alpha stage and may change significantly. Behavior,
> configuration and the user interface can change between versions, including in ways that break
> existing helpers. Use it with that in mind.

---

## For users

### What is this?

You create a normal template sensor (name, state template, unit, device/state class, icon) and then
add custom attributes to it. Every attribute has a name and **its own template**.

The attributes are edited in the **Template Attributes** panel in the sidebar:

- On the left there is the **list of your helpers**, sorted by name, with a **search field** on top
  (parts of the name are enough). The helper you select is edited on the right.
- Templates are edited with Home Assistant's standard template editor (syntax highlighting,
  autocomplete for entities and functions).
- Each attribute is **one collapsed section**. The title shows the **name and the current value**
  (`double = 84`), so you get an overview of everything at a glance.
- Below the last section there is an input field for the name of a new attribute and an
  **Add attribute** button. The new section opens so you can enter its template; below it you find the
  field for the next attribute.
- Behind every attribute name there is a small **trash icon** that deletes the attribute together
  with its template.
- **Save** validates everything and applies it immediately - no restart needed.

### Quick start

1. Settings → Devices & services → Helpers → **Create helper** → **Template Attributes**.
   Enter a name and a state template, e.g. `{{ states('sensor.outdoor_temperature') }}`.
2. Open **Template Attributes** in the sidebar. Type a name (e.g. `fahrenheit`), press
   **Add attribute**, and enter a template, e.g. `{{ (state | float * 9 / 5 + 32) | round(1) }}`.
3. Press **Save**.

Inside an attribute template the variable `state` holds the current state of the sensor. The result
keeps its type: numbers, lists and objects stay numbers, lists and objects.

Attribute names may contain letters, digits and `_` (no leading digit), must be unique and must not
be a name Home Assistant reserves (`friendly_name`, `icon`, `unit_of_measurement`, `device_class`,
`state_class`, ...).

The settings of the standard sensor (state template, unit, ...) can be changed later with the
helper's **Options** (the panel links to them). Vice versa, the Options contain a **Manage
attributes of this helper** link below the form that opens the panel directly with that helper
selected.

The sidebar entry can be hidden like any other one (sidebar settings in your user profile); the
panel stays reachable through that link and at `/template-attributes`.

If a template fails at runtime, the error is logged, the last good value is kept and all other
attributes keep working. More: see [`examples/en/`](examples/en/README.md).

---

## For developers

- Spec: [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) (German). Update it with every behavior change.
- Open the repo in the devcontainer (`.devcontainer/`), then:

  ```bash
  python -m pytest                      # mocked HA: flow, sensor, websocket API, translations
  pip install -r requirements_e2e.txt
  python -m playwright install --with-deps chromium
  python -m pytest tests_e2e            # real HA + real frontend + headless Chromium
  ```

  Open the screenshots in `tests_e2e/screenshots/` after an e2e run.
- Layout: `config_flow.py` (standard sensor), `sensor.py`, `validation.py` (shared checks),
  `websocket_api.py` (list/save for the panel), `www/template-attributes-panel.js` (panel, plain
  JS, no build step).
- Conventional Commits drive semantic-release (`feat` minor, `fix` patch, `feat!` major).

---

# Deutsch

[English version](#template-attributes-home-assistant-helper) (weiter oben in dieser Datei)

Eine HACS-Integration für einen Template-Sensor mit **beliebig vielen zusätzlichen Attributen**, jedes
mit eigenem Jinja2-Template – komplett über die Home-Assistant-Oberfläche, ohne YAML.

> [!WARNING]
> **Alpha:** Dieses Projekt befindet sich noch in einem frühen Alpha-Stadium und kann sich stark
> ändern. Verhalten, Konfiguration und Oberfläche können sich zwischen Versionen ändern – auch so,
> dass bestehende Helfer nicht mehr funktionieren. Bitte mit diesem Hintergrund verwenden.

## Für Anwender

### Was ist das?

Du legst einen normalen Template-Sensor an (Name, State-Template, Einheit, Geräte-/Statusklasse,
Icon) und fügst ihm eigene Attribute hinzu. Jedes Attribut hat einen Namen und **ein eigenes Template**.

Die Attribute bearbeitest du im Panel **Template Attributes** in der Seitenleiste:

- Links steht die **Liste deiner Helfer**, nach Name sortiert, mit einem **Suchfeld** darüber
  (Teile des Namens genügen). Der gewählte Helfer wird rechts daneben bearbeitet.
- Templates bearbeitest du mit dem Standard-Template-Editor von Home Assistant (Syntax-Hervorhebung,
  Autovervollständigung für Entitäten und Funktionen).
- Jedes Attribut ist **ein eingeklappter Abschnitt**. Der Titel zeigt **Name und aktuellen Wert**
  (`double = 84`) – so siehst du alles auf einen Blick.
- Unter dem letzten Abschnitt steht ein Eingabefeld für den Namen eines neuen Attributs mit dem Button
  **Attribut hinzufügen**. Der neue Abschnitt öffnet sich, damit du das Template eingeben kannst;
  darunter folgt wieder das Feld für das nächste Attribut.
- Hinter jedem Attributnamen sitzt ein kleiner **Papierkorb**, der das Attribut samt Template löscht.
- **Speichern** prüft alles und übernimmt es sofort – kein Neustart nötig.

### Schnellstart

1. Einstellungen → Geräte & Dienste → Helfer → **Helfer erstellen** → **Template Attributes**.
   Name und State-Template eingeben, z. B. `{{ states('sensor.aussentemperatur') }}`.
2. In der Seitenleiste **Template Attributes** öffnen. Namen eintippen (z. B. `fahrenheit`),
   **Attribut hinzufügen** drücken und ein Template eingeben, z. B.
   `{{ (state | float * 9 / 5 + 32) | round(1) }}`.
3. **Speichern** drücken.

Im Attribut-Template enthält die Variable `state` den aktuellen Zustand des Sensors. Das Ergebnis
behält seinen Typ: Zahlen, Listen und Objekte bleiben Zahlen, Listen und Objekte.

Attributnamen bestehen aus Buchstaben, Ziffern und `_` (keine Ziffer am Anfang), müssen eindeutig sein
und dürfen kein von Home Assistant reservierter Name sein (`friendly_name`, `icon`,
`unit_of_measurement`, `device_class`, `state_class`, ...).

Die Einstellungen des Standard-Sensors (State-Template, Einheit, ...) änderst du später über die
**Optionen** des Helfers (das Panel verlinkt dorthin). Umgekehrt enthalten die Optionen unter dem
Formular einen Link **Attribute dieses Helfers verwalten**, der das Panel direkt mit diesem Helfer
öffnet.

Den Seitenleisten-Eintrag kannst du wie jeden anderen ausblenden (Seitenleisten-Einstellungen im
Benutzerprofil); das Panel bleibt über diesen Link und unter `/template-attributes` erreichbar.

Schlägt ein Template zur Laufzeit fehl, wird der Fehler geloggt, der letzte gute Wert bleibt erhalten
und alle anderen Attribute laufen weiter. Mehr: siehe [`examples/de/`](examples/de/README.md).
