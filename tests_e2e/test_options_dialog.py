"""Real browser against a real Home Assistant: editing attributes in the options dialog.

Attributes are form sections in the standard options dialog: title = attribute name, change the name
to rename, a switch deletes, a tick box adds new ones through the attribute step. Screenshots land in
tests_e2e/screenshots (open them after a run).
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

SHOTS = Path(__file__).parent / "screenshots"
ENTITY = "sensor.e2e_demo"


def _api(page, method: str, path: str, body: dict | None = None):
    """Call the HA REST API with the access token the logged-in session keeps in localStorage."""
    return page.evaluate(
        """async ([method, path, body]) => {
            const tokens = JSON.parse(localStorage.getItem("hassTokens"));
            const res = await fetch(path, {
                method,
                headers: {"Authorization": "Bearer " + tokens.access_token,
                          "Content-Type": "application/json"},
                body: body ? JSON.stringify(body) : undefined,
            });
            return await res.json();
        }""",
        [method, path, body],
    )


def _flow(page, step_input: dict | None = None, flow_id: str | None = None):
    path = "/api/config/config_entries/flow"
    if flow_id is None:
        return _api(page, "POST", path, {"handler": "template_attributes"})
    return _api(page, "POST", f"{path}/{flow_id}", step_input)


@pytest.fixture
def helper(page, ha_base_url):
    """A helper "E2E Demo" with two attributes, created through the real create flow."""
    page.goto(ha_base_url + "/")
    page.wait_for_load_state("networkidle")
    flow = _flow(page)
    result = _flow(
        page, {"name": "E2E Demo", "state_template": "{{ 40 + 2 }}"}, flow["flow_id"]
    )
    assert result["step_id"] == "attribute", result
    result = _flow(
        page,
        {"name": "double", "template": "{{ state * 2 }}", "add_another": True},
        flow["flow_id"],
    )
    assert result["step_id"] == "attribute", result
    result = _flow(
        page, {"name": "note", "template": "hello", "add_another": False}, flow["flow_id"]
    )
    assert result["type"] == "create_entry", result
    entry_id = result["result"]["entry_id"]
    yield entry_id
    _api(page, "DELETE", f"/api/config/config_entries/entry/{entry_id}")


def _attributes(page) -> dict:
    return _api(page, "GET", f"/api/states/{ENTITY}").get("attributes", {})


def _wait_for_attributes(page, predicate, timeout: float = 15):
    deadline = time.monotonic() + timeout
    attrs = {}
    while time.monotonic() < deadline:
        attrs = _attributes(page)
        if predicate(attrs):
            return attrs
        time.sleep(0.5)
    raise AssertionError(f"attributes never matched, last seen: {attrs}")


def _open_options(page):
    page.goto("/config/integrations/integration/template_attributes")
    row = page.locator("ha-integration-card, ha-config-entry-row").filter(has_text="E2E Demo")
    row.get_by_role("button", name="Configure").click()
    page.get_by_text("Add a new attribute after saving").wait_for()


def _section(page, index: int):
    """The n-th attribute section of the dialog (they follow the order of the attributes)."""
    return page.locator("ha-form-expandable").nth(index)


def test_created_through_the_flow_the_attributes_exist(page, helper):
    attrs = _wait_for_attributes(page, lambda a: "note" in a)
    assert attrs["double"] == 84
    assert attrs["note"] == "hello"


def test_sections_rename_and_delete(page, helper):
    SHOTS.mkdir(exist_ok=True)
    _open_options(page)
    # one collapsed section per attribute, titled with the attribute name
    page.get_by_text("double", exact=True).scroll_into_view_if_needed()
    assert page.locator("ha-form-expandable").count() == 2
    page.screenshot(path=str(SHOTS / "options-sections-collapsed.png"))

    # open both: rename "double", delete "note" with its switch
    page.get_by_text("double", exact=True).click()
    page.get_by_text("note", exact=True).click()
    _section(page, 0).locator("input[type=text]").fill("twice")
    _section(page, 1).get_by_text("Delete this attribute").first.click()
    _section(page, 1).scroll_into_view_if_needed()
    page.screenshot(path=str(SHOTS / "options-sections-open.png"))

    page.get_by_role("button", name="Submit").click()

    # nothing is applied yet: a confirmation lists what will be deleted and renamed
    page.get_by_text("These changes will be applied").wait_for()
    assert page.get_by_text("Deleted:").count() >= 1
    assert page.get_by_text("double → twice").count() >= 1
    assert "note" in _attributes(page)
    page.screenshot(path=str(SHOTS / "options-confirm.png"))
    page.get_by_role("button", name="Submit").click()

    attrs = _wait_for_attributes(page, lambda a: "twice" in a and "note" not in a)
    assert attrs["twice"] == 84
    assert "double" not in attrs


def test_tick_box_adds_attributes_one_after_the_other(page, helper):
    SHOTS.mkdir(exist_ok=True)
    _open_options(page)
    page.get_by_text("Add a new attribute after saving").click()
    page.get_by_role("button", name="Submit").click()

    # first new attribute, "add another" ticked
    page.get_by_text("Attributes so far: double, note").wait_for()
    page.locator("step-flow-form input[type=text]").first.fill("third")
    page.locator("step-flow-form .cm-content").first.click()
    page.locator("step-flow-form .cm-content").first.fill("{{ state + 1 }}")
    page.get_by_text("Add another attribute after this one").click()
    page.screenshot(path=str(SHOTS / "options-attribute-step.png"))
    page.get_by_role("button", name="Submit").click()

    # a fresh form lists what exists now; leave the name empty to finish
    page.get_by_text("Attributes so far: double, note, third").wait_for()
    page.get_by_role("button", name="Submit").click()

    attrs = _wait_for_attributes(page, lambda a: "third" in a)
    assert attrs["third"] == 43
    assert attrs["double"] == 84
    assert attrs["note"] == "hello"
