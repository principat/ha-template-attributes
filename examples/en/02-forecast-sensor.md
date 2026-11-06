# 02 - Forecast sensor

A sensor whose state is the current value and whose `forecast` attribute is a list of future
values (`time` / `value`), one per hour for the next 24 hours. `sensor.outdoor_temperature` is an
example entity id - use your own. The "forecast" here is a simple linear trend, replace the
calculation with your own logic.

> [!TIP]
> **This is much easier with [ha-template-forecast](https://github.com/principat/ha-template-forecast).**
> It is built for exactly this: you set the number of steps and the step size, write a template
> that is evaluated once per step (or transform the forecast of an existing entity), and it builds
> the list for you - no loop, no `namespace`. Use Template Attributes for a forecast only if you
> need other attributes next to it or want to keep everything in one helper.

**Helper** (Create helper → Template Attributes)

| Field | Value |
|---|---|
| Name | `Outdoor temperature forecast` |
| State template | `{{ states('sensor.outdoor_temperature') }}` |
| Unit | `°C` |
| Device class | `temperature` |
| Recalculation interval | `60` |

**Attributes** (the "Add attribute" step when creating, later in the helper options)

| Name | Template |
|---|---|
| `forecast` | see below |

```jinja
{% set ns = namespace(items=[]) %}
{% for i in range(24) %}
  {% set ns.items = ns.items + [{
    'time': (now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=i)).isoformat(),
    'value': (state | float + i * 0.5) | round(1)
  }] %}
{% endfor %}
{{ ns.items }}
```

`state` is the current state of the sensor, `i` is the hour offset. The result stays a real list
of objects, so you can use it in automations and dashboards (`state_attr(..., 'forecast')`).

Notes:

- The attributes of the entity contain `forecast` as a list of objects with `time` and `value`.
- Home Assistant stores state attributes in the database. Very long lists make every state change
  large - keep the number of steps reasonable.
