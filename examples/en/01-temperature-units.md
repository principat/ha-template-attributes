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

**Attributes** (the "Add attribute" step when creating, later in the helper options)

| Name | Template |
|---|---|
| `fahrenheit` | `{{ (state \| float * 9 / 5 + 32) \| round(1) }}` |
| `kelvin` | `{{ (state \| float + 273.15) \| round(2) }}` |

The attributes of the entity then contain `fahrenheit: 68.0` and `kelvin: 293.15`.
