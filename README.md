# Template Attributes (Home Assistant Helper)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=principat&repository=ha-template-attributes&category=integration)

**English** | [Deutsche Version](#deutsch) (further down in this file)

A HACS custom integration for a template sensor with **any number of extra attributes**, each with
its own Jinja2 template - entirely through the standard Home Assistant dialogs, no YAML.

> [!WARNING]
> **Alpha:** This project is still in an early alpha stage and may change significantly. Behavior,
> configuration and the user interface can change between versions, including in ways that break
> existing helpers. Use it with that in mind.

---

## For users

### What is this?

You create a normal template sensor (name, state template, unit, device/state class, icon) and add
custom attributes to it. Every attribute has a name and **its own template**. Everything happens in
the normal helper dialogs:

- **Create helper → Template Attributes**: first the standard sensor, then an **Add attribute** step
  (name and template). Tick **Add another attribute after this one** to save the attribute and get a
  new empty one right away; leave the name empty to finish.
- **Options of the helper** (gear icon): the standard sensor settings and, below them, **one
  collapsed section per attribute** - the title is the attribute name.
  - Change the **name** inside the section to **rename** the attribute.
  - Switch on **Delete this attribute** to remove it. A Home Assistant form cannot grey out fields
    while you edit, so after **Submit** a **confirmation** lists what will be deleted and renamed;
    nothing is changed before you confirm (or tick the box to go back and edit).
  - Tick **Add a new attribute after saving** at the bottom to add attributes with the same step as
    when creating.
- Templates are edited with Home Assistant's standard template editor (syntax highlighting, autocomplete).

### Quick start

1. Settings → Devices & services → Helpers → **Create helper** → **Template Attributes**.
   Enter a name and a state template, e.g. `{{ states('sensor.outdoor_temperature') }}`.
2. In the next step enter an attribute name (e.g. `fahrenheit`) and a template, e.g.
   `{{ (state | float * 9 / 5 + 32) | round(1) }}`. Leave **Add another** unticked and press **Submit**.

Inside an attribute template the variable `state` holds the current state of the sensor. The result
keeps its type: numbers, lists and objects stay numbers, lists and objects.

Attribute names may contain letters, digits and `_` (no leading digit), must be unique and must not
be a name Home Assistant reserves (`friendly_name`, `icon`, `unit_of_measurement`, `device_class`,
`state_class`, ...) or a field name of the form (`state_template`, `update_interval_minutes`,
`add_attribute`). A problem with a name or template is reported with the attribute's name and nothing
is saved.

The names of the fields inside an attribute section ("Name", "Template", "Delete this attribute") follow
the language set for the Home Assistant server, not the one of your user profile.

If a template fails at runtime, the error is logged, the last good value is kept and all other
attributes keep working. More: see [`examples/en/`](examples/en/README.md).

---

## For developers

- Spec: [`docs/REQUIREMENTS.md`](docs/REQUIREMENTS.md) (German). Update it with every behavior change.
- Open the repo in the devcontainer (`.devcontainer/`), then:

  ```bash
  python -m pytest                      # mocked HA: flows, sensor, translations
  pip install -r requirements_e2e.txt
  python -m playwright install --with-deps chromium
  python -m pytest tests_e2e            # real HA + real frontend + headless Chromium
  ```

  Open the screenshots in `tests_e2e/screenshots/` after an e2e run.
- Layout: `config_flow.py` (create flow, options flow with one section per attribute, shared attribute
  step), `sensor.py`, `validation.py` (shared checks). There is no frontend code.
- Conventional Commits drive semantic-release (`feat` minor, `fix` patch, `feat!` major).

---

# Deutsch

[English version](#template-attributes-home-assistant-helper) (weiter oben in dieser Datei)

Eine HACS-Integration für einen Template-Sensor mit **beliebig vielen zusätzlichen Attributen**, jedes
mit eigenem Jinja2-Template – komplett über die Standard-Dialoge von Home Assistant, ohne YAML.

> [!WARNING]
> **Alpha:** Dieses Projekt befindet sich noch in einem frühen Alpha-Stadium und kann sich stark
> ändern. Verhalten, Konfiguration und Oberfläche können sich zwischen Versionen ändern – auch so,
> dass bestehende Helfer nicht mehr funktionieren. Bitte mit diesem Hintergrund verwenden.

## Für Anwender

### Was ist das?

Du legst einen normalen Template-Sensor an (Name, State-Template, Einheit, Geräte-/Statusklasse,
Icon) und fügst ihm eigene Attribute hinzu. Jedes Attribut hat einen Namen und **ein eigenes
Template**. Alles geschieht in den normalen Helfer-Dialogen:

- **Helfer erstellen → Template Attributes**: zuerst der Standard-Sensor, danach ein Schritt
  **Attribut hinzufügen** (Name und Template). Mit dem Haken **Danach ein weiteres Attribut
  hinzufügen** wird das Attribut übernommen und sofort ein neues, leeres geöffnet; zum Abschließen den
  Namen leer lassen.
- **Optionen des Helfers** (Zahnrad): die Einstellungen des Standard-Sensors und darunter **ein
  eingeklappter Abschnitt pro Attribut** – der Titel ist der Attributname.
  - Den **Namen** im Abschnitt zu ändern **benennt** das Attribut um.
  - Der Schalter **Dieses Attribut löschen** entfernt es. Ein Home-Assistant-Formular kann Felder
    nicht während der Eingabe ausgrauen; deshalb listet nach **Absenden** eine **Bestätigung**, was
    gelöscht und umbenannt wird. Vorher ändert sich nichts (oder mit dem Haken zurück und weiter
    bearbeiten).
  - Mit dem Haken **Nach dem Speichern ein neues Attribut hinzufügen** unten legst du neue Attribute
    mit demselben Schritt an wie beim Erstellen.
- Templates bearbeitest du mit dem Standard-Template-Editor von Home Assistant (Syntax-Hervorhebung,
  Autovervollständigung).

### Schnellstart

1. Einstellungen → Geräte & Dienste → Helfer → **Helfer erstellen** → **Template Attributes**.
   Name und State-Template eingeben, z. B. `{{ states('sensor.aussentemperatur') }}`.
2. Im nächsten Schritt einen Attributnamen (z. B. `fahrenheit`) und ein Template eingeben, z. B.
   `{{ (state | float * 9 / 5 + 32) | round(1) }}`. **Weiteres Attribut** nicht ankreuzen und
   **Absenden** drücken.

Im Attribut-Template enthält die Variable `state` den aktuellen Zustand des Sensors. Das Ergebnis
behält seinen Typ: Zahlen, Listen und Objekte bleiben Zahlen, Listen und Objekte.

Attributnamen bestehen aus Buchstaben, Ziffern und `_` (keine Ziffer am Anfang), müssen eindeutig sein
und dürfen weder ein von Home Assistant reservierter Name (`friendly_name`, `icon`,
`unit_of_measurement`, `device_class`, `state_class`, ...) noch ein Feldname des Formulars
(`state_template`, `update_interval_minutes`, `add_attribute`) sein. Ein Problem mit Name oder Template
wird mit dem Attributnamen gemeldet, und es wird nichts gespeichert.

Die Bezeichnungen der Felder innerhalb eines Attribut-Abschnitts („Name“, „Template“, „Dieses Attribut
löschen“) richten sich nach der Sprache des Home-Assistant-Servers, nicht nach der des
Benutzerprofils.

Schlägt ein Template zur Laufzeit fehl, wird der Fehler geloggt, der letzte gute Wert bleibt erhalten
und alle anderen Attribute laufen weiter. Mehr: siehe [`examples/de/`](examples/de/README.md).
