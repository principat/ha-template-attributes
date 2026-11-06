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

**Attribute** (Seitenleiste → Template Attributes)

| Name | Template |
|---|---|
| `fahrenheit` | `{{ (state \| float * 9 / 5 + 32) \| round(1) }}` |
| `kelvin` | `{{ (state \| float + 273.15) \| round(2) }}` |

Im Panel lauten die eingeklappten Abschnitte dann `fahrenheit = 68.0`, `kelvin = 293.15`.
