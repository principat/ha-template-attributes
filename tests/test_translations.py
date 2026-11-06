"""Translation files stay in sync and only use placeholders the code provides."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from custom_components.template_attributes import validation

COMPONENT = Path(__file__).parents[1] / "custom_components" / "template_attributes"
FILES = {
    "strings": COMPONENT / "strings.json",
    "en": COMPONENT / "translations" / "en.json",
    "de": COMPONENT / "translations" / "de.json",
}


def _load(name: str) -> dict:
    return json.loads(FILES[name].read_text(encoding="utf-8"))


def _flatten(node: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            out.update(_flatten(value, path))
        else:
            out[path] = value
    return out


def test_en_and_strings_are_identical() -> None:
    assert _load("strings") == _load("en")


def test_de_has_exactly_the_keys_of_en() -> None:
    assert set(_flatten(_load("de"))) == set(_flatten(_load("en")))


@pytest.mark.parametrize("lang", ["en", "de"])
def test_placeholders_match_between_languages(lang: str) -> None:
    en, other = _flatten(_load("en")), _flatten(_load(lang))
    pattern = re.compile(r"\{(\w+)\}")
    for key, text in en.items():
        assert set(pattern.findall(text)) == set(pattern.findall(other[key])), key


@pytest.mark.parametrize("lang", ["en", "de"])
def test_every_error_code_of_the_flow_is_translated(lang: str) -> None:
    errors = _load(lang)["config"]["error"]
    for code in (validation.ERR_INVALID_TEMPLATE, validation.ERR_RENDER):
        assert code in errors
    assert errors == _load(lang)["options"]["error"]


def test_all_flow_fields_have_a_label() -> None:
    from custom_components.template_attributes import config_flow

    for with_name, section in ((True, "config.step.user"), (False, "options.step.init")):
        labels = _flatten(_load("en"))
        for field in config_flow._schema({}, with_name).schema:
            assert f"{section}.data.{field}" in labels, (section, str(field))
