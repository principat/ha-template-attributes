# 01 – Temperatur in mehreren Einheiten

Ein Sensor, dessen Zustand °C ist und dessen Attribute dieselbe Temperatur in anderen Einheiten
liefern. `sensor.aussentemperatur` ist eine Beispiel-Entity-ID – eigene verwenden.

**Helfer** (Helfer erstellen → Template Attributes)

| Feld | Wert |
|---|---|
| Name | `Außentemperatur` |
| State-Template | `{{ states('sensor.aussentemperatur') }}` |
| Einheit | `°C` |
| Geräteklasse | `temperature` |

**Attribute** (Schritt „Attribut hinzufügen“ beim Erstellen, später in den Optionen des Helfers)

| Name | Template |
|---|---|
| `fahrenheit` | `{{ (state \| float * 9 / 5 + 32) \| round(1) }}` |
| `kelvin` | `{{ (state \| float + 273.15) \| round(2) }}` |

In den Attributen der Entität stehen dann `fahrenheit: 68.0` und `kelvin: 293.15`.
