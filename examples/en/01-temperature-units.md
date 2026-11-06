# 01 - Temperature in several units

One sensor whose state is °C and whose attributes give the same temperature in other units.
`sensor.outdoor_temperature` is an example entity id - use your own.

**Helper** (Create helper → Template Attributes)

| Field | Value |
|---|---|
| Name | `Outdoor temperature` |
| State template | `{{ states('sensor.outdoor_temperature') }}` |
| Unit | `°C` |
| Device class | `temperature` |

**Attributes** (sidebar → Template Attributes)

| Name | Template |
|---|---|
| `fahrenheit` | `{{ (state \| float * 9 / 5 + 32) \| round(1) }}` |
| `kelvin` | `{{ (state \| float + 273.15) \| round(2) }}` |

In the panel the collapsed sections then read `fahrenheit = 68.0`, `kelvin = 293.15`.
