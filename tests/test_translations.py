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
    for code in (
        validation.ERR_INVALID_TEMPLATE,
        validation.ERR_RENDER,
        validation.ERR_ATTRIBUTE_INVALID_TEMPLATE,
        validation.ERR_ATTRIBUTE_RENDER,
        validation.ERR_INVALID_NAME,
        validation.ERR_RESERVED_NAME,
        validation.ERR_DUPLICATE_NAME,
    ):
        assert code in errors
    assert errors == _load(lang)["options"]["error"]


def test_all_flow_fields_have_a_label() -> None:
    from custom_components.template_attributes import config_flow

    labels = _flatten(_load("en"))
    forms = {
        "config.step.user": config_flow._schema({}, with_name=True),
        "config.step.attribute": config_flow._attribute_schema().schema,
        "options.step.attribute": config_flow._attribute_schema().schema,
        "options.step.confirm": {"go_back": None},
        # sections are dynamic (named like the attribute), their field labels come from code
        "options.step.init": config_flow.options_schema(
            {}, [], config_flow.section_labels("en")
        ).schema,
    }
    for step, fields in forms.items():
        for field in fields:
            assert f"{step}.data.{field}" in labels, (step, str(field))


def test_section_labels_exist_for_every_language() -> None:
    from custom_components.template_attributes import config_flow

    assert set(config_flow.SECTION_LABELS) == {"en", "de"}
    for texts in config_flow.SECTION_LABELS.values():
        assert set(texts) == {"name", "template", "delete", "deleted", "renamed"}
    assert config_flow.section_labels("de-AT")["delete"].startswith("Dieses")
    assert config_flow.section_labels(None) == config_flow.SECTION_LABELS["en"]
