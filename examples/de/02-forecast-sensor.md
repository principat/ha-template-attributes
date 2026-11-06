# 02 – Forecast-Sensor

Ein Sensor, dessen Zustand der aktuelle Wert ist und dessen Attribut `forecast` eine Liste
zukünftiger Werte (`time` / `value`) enthält, einen pro Stunde für die nächsten 24 Stunden.
`sensor.aussentemperatur` ist eine Beispiel-Entity-ID – eigene verwenden. Die „Vorhersage“ ist hier
nur ein einfacher linearer Trend, die Berechnung durch eigene Logik ersetzen.

> [!TIP]
> **Mit [ha-template-forecast](https://github.com/principat/ha-template-forecast) geht das deutlich
> einfacher.** Es ist genau dafür gebaut: Du legst Anzahl und Länge der Schritte fest, schreibst ein
> Template, das einmal pro Schritt ausgewertet wird (oder wandelst die Vorhersage einer bestehenden
> Entität um), und die Liste wird für dich gebaut – ohne Schleife und ohne `namespace`. Template
> Attributes lohnt sich für eine Vorhersage nur, wenn daneben weitere Attribute nötig sind oder alles
> in einem Helfer liegen soll.

**Helfer** (Helfer erstellen → Template Attributes)

| Feld | Wert |
|---|---|
| Name | `Außentemperatur Vorhersage` |
| State-Template | `{{ states('sensor.aussentemperatur') }}` |
| Einheit | `°C` |
| Geräteklasse | `temperature` |
| Neuberechnungsintervall | `60` |

**Attribute** (Seitenleiste → Template Attributes)

| Name | Template |
|---|---|
| `forecast` | siehe unten |

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

`state` ist der aktuelle Zustand des Sensors, `i` der Stunden-Offset. Das Ergebnis bleibt eine echte
Liste von Objekten und lässt sich in Automationen und Dashboards verwenden
(`state_attr(..., 'forecast')`).

Hinweise:

- Im Panel lautet der Abschnitt `forecast = [{"time": "...", "value": 20.0}, ...]`.
- Home Assistant speichert Zustandsattribute in der Datenbank. Sehr lange Listen machen jede
  Zustandsänderung groß – die Anzahl der Schritte in Maßen halten.
