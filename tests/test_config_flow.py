"""Tests for the config and options flow (standard sensor + attribute steps + sections)."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.template_attributes.config_flow import section_labels
from custom_components.template_attributes.const import (
    CONF_ADD_ANOTHER,
    CONF_ADD_ATTRIBUTE,
    CONF_ATTRIBUTES,
    CONF_NAME,
    CONF_STATE_TEMPLATE,
    DOMAIN,
)

LABELS = section_labels("en")


async def _start(hass: HomeAssistant, user_input: dict):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    return await hass.config_entries.flow.async_configure(result["flow_id"], user_input)


async def _attribute(hass, flow_id, name, template="", another=False):
    return await hass.config_entries.flow.async_configure(
        flow_id,
        {"name": name, "template": template, CONF_ADD_ANOTHER: another},
    )


# --- create -----------------------------------------------------------------------------------


async def test_create_goes_on_to_the_attribute_step(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 1 + 1 }}"})

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "attribute"
    assert result["description_placeholders"]["attributes"] == "—"


async def test_empty_name_skips_the_attribute_step(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 1 + 1 }}"})
    result = await _attribute(hass, result["flow_id"], "")

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Demo"
    assert result["data"][CONF_STATE_TEMPLATE] == "{{ 1 + 1 }}"
    assert result["data"][CONF_ATTRIBUTES] == []


async def test_add_another_repeats_the_attribute_step(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 21 }}"})
    result = await _attribute(hass, result["flow_id"], "double", "{{ state * 2 }}", another=True)

    # a fresh, empty form that lists what has been added so far
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "attribute"
    assert result["description_placeholders"]["attributes"] == "double"

    result = await _attribute(hass, result["flow_id"], "note", "hello")
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_ATTRIBUTES] == [
        {"name": "double", "template": "{{ state * 2 }}"},
        {"name": "note", "template": "hello"},
    ]


async def test_invalid_template_syntax_is_reported_on_the_field(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 1 + "})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_STATE_TEMPLATE: "invalid_template"}
    assert result["description_placeholders"]["template_error"]


async def test_render_error_is_reported_on_the_field(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 1 / 0 }}"})

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {CONF_STATE_TEMPLATE: "template_render_error"}


async def test_attribute_step_reports_problems_and_stays(hass: HomeAssistant) -> None:
    result = await _start(hass, {CONF_NAME: "Demo", CONF_STATE_TEMPLATE: "{{ 1 }}"})
    flow_id = result["flow_id"]

    for name, template, code in (
        ("1bad", "", "invalid_attribute_name"),
        ("icon", "", "reserved_attribute_name"),
        ("add_attribute", "", "reserved_attribute_name"),
        ("broken", "{{ 1 + ", "attribute_invalid_template"),
        ("boom", "{{ 1 / 0 }}", "attribute_template_render_error"),
    ):
        result = await _attribute(hass, flow_id, name, template)
        assert result["type"] == FlowResultType.FORM, name
        assert result["errors"] == {"base": code}, name
        assert result["description_placeholders"]["attribute"] == name

    # a duplicate of an attribute added before
    await _attribute(hass, flow_id, "ok", "x", another=True)
    result = await _attribute(hass, flow_id, "ok", "y")
    assert result["errors"] == {"base": "duplicate_attribute_name"}


# --- options ----------------------------------------------------------------------------------


def _section(name=None, template=None, delete=False) -> dict:
    return {LABELS["name"]: name, LABELS["template"]: template, LABELS["delete"]: delete}


async def _options(hass, entry, user_input=None):
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    if user_input is None:
        return result
    return await hass.config_entries.options.async_configure(result["flow_id"], user_input)


def _entry_with(hass, make_entry):
    entry = make_entry("{{ 21 }}", attributes=[("double", "{{ state * 2 }}"), ("note", "hi")])
    return entry


async def test_options_form_has_one_section_per_attribute(hass: HomeAssistant, make_entry) -> None:
    entry = _entry_with(hass, make_entry)
    result = await _options(hass, entry)

    keys = [str(key) for key in result["data_schema"].schema]
    assert "double" in keys and "note" in keys
    assert keys[-1] == CONF_ADD_ATTRIBUTE  # the tick box stays at the bottom


async def test_options_keep_attributes_when_only_the_sensor_changes(
    hass: HomeAssistant, make_entry
) -> None:
    entry = _entry_with(hass, make_entry)
    result = await _options(
        hass,
        entry,
        {
            CONF_STATE_TEMPLATE: "{{ 2 }}",
            "double": _section("double", "{{ state * 2 }}"),
            "note": _section("note", "hi"),
        },
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_STATE_TEMPLATE] == "{{ 2 }}"
    assert entry.options[CONF_ATTRIBUTES] == [
        {"name": "double", "template": "{{ state * 2 }}"},
        {"name": "note", "template": "hi"},
    ]


async def _confirm(hass, result, go_back=False):
    return await hass.config_entries.options.async_configure(
        result["flow_id"], {"go_back": go_back}
    )


async def test_changing_the_name_renames_and_a_switch_deletes_after_confirming(
    hass: HomeAssistant, make_entry
) -> None:
    entry = _entry_with(hass, make_entry)
    result = await _options(
        hass,
        entry,
        {
            CONF_STATE_TEMPLATE: "{{ 21 }}",
            "double": _section("twice", "{{ state * 2 }}"),
            "note": _section("note", "hi", delete=True),
        },
    )

    # nothing is saved yet: the user first sees what will happen
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "confirm"
    changes = result["description_placeholders"]["changes"]
    assert "Deleted:** note" in changes
    assert "Renamed:** double → twice" in changes
    assert CONF_ATTRIBUTES not in entry.options

    result = await _confirm(hass, result)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ATTRIBUTES] == [{"name": "twice", "template": "{{ state * 2 }}"}]


async def test_going_back_from_the_confirmation_keeps_what_was_typed(
    hass: HomeAssistant, make_entry
) -> None:
    entry = _entry_with(hass, make_entry)
    result = await _options(
        hass,
        entry,
        {
            CONF_STATE_TEMPLATE: "{{ 21 }}",
            "double": _section("twice", "{{ state * 2 }}"),
            "note": _section("note", "hi", delete=True),
        },
    )
    result = await _confirm(hass, result, go_back=True)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    assert CONF_ATTRIBUTES not in entry.options
    schema = result["data_schema"].schema
    typed = {
        str(key): key.default() for key in schema["double"].schema.schema
    }
    assert typed[LABELS["name"]] == "twice"
    deleted = {str(key): key.default() for key in schema["note"].schema.schema}
    assert deleted[LABELS["delete"]] is True


async def test_options_report_a_bad_attribute_and_keep_what_was_typed(
    hass: HomeAssistant, make_entry
) -> None:
    entry = _entry_with(hass, make_entry)
    result = await _options(
        hass,
        entry,
        {
            CONF_STATE_TEMPLATE: "{{ 21 }}",
            "double": _section("double", "{{ 1 + "),
            "note": _section("note", "hi"),
        },
    )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "attribute_invalid_template"}
    assert result["description_placeholders"]["attribute"] == "double"
    assert CONF_ATTRIBUTES not in entry.options  # nothing was saved

    # renaming two attributes to the same name is caught as well
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_STATE_TEMPLATE: "{{ 21 }}",
            "double": _section("same", "x"),
            "note": _section("same", "y"),
        },
    )
    assert result["errors"] == {"base": "duplicate_attribute_name"}


async def test_a_deleted_attribute_is_not_validated(hass: HomeAssistant, make_entry) -> None:
    entry = _entry_with(hass, make_entry)
    result = await _options(
        hass,
        entry,
        {
            CONF_STATE_TEMPLATE: "{{ 21 }}",
            "double": _section("double", "{{ 1 + ", delete=True),
            "note": _section("note", "hi"),
        },
    )
    assert result["step_id"] == "confirm"  # no validation error for the deleted attribute
    result = await _confirm(hass, result)

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_ATTRIBUTES] == [{"name": "note", "template": "hi"}]


async def test_options_can_add_attributes_one_after_the_other(
    hass: HomeAssistant, make_entry
) -> None:
    entry = _entry_with(hass, make_entry)
    result = await _options(
        hass,
        entry,
        {
            CONF_STATE_TEMPLATE: "{{ 21 }}",
            "double": _section("double", "{{ state * 2 }}"),
            "note": _section("note", "hi", delete=True),
            CONF_ADD_ATTRIBUTE: True,
        },
    )
    assert result["step_id"] == "confirm"  # note is deleted
    result = await _confirm(hass, result)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "attribute"
    assert result["description_placeholders"]["attributes"] == "double"
    assert CONF_ATTRIBUTES not in entry.options  # saved only at the end

    flow_id = result["flow_id"]
    result = await hass.config_entries.options.async_configure(
        flow_id, {"name": "third", "template": "{{ state + 1 }}", CONF_ADD_ANOTHER: True}
    )
    assert result["step_id"] == "attribute"
    result = await hass.config_entries.options.async_configure(
        flow_id, {"name": "fourth", "template": "4", CONF_ADD_ANOTHER: False}
    )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert [a["name"] for a in entry.options[CONF_ATTRIBUTES]] == ["double", "third", "fourth"]


async def test_options_keep_other_options(hass: HomeAssistant, make_entry) -> None:
    entry = make_entry("{{ 1 }}")
    hass.config_entries.async_update_entry(entry, options={"icon": "mdi:flash"})
    result = await _options(hass, entry, {CONF_STATE_TEMPLATE: "{{ 2 }}"})

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options["icon"] == "mdi:flash"
    assert entry.options[CONF_ATTRIBUTES] == []
