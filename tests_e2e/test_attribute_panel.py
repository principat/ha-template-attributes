"""Real browser against a real Home Assistant: the attribute editor panel.

Mocked tests cannot show what the user sees. This one creates a helper through the real config
flow API, opens the sidebar panel and checks the behavior that was asked for: sections are closed,
titles show "name = value", attributes are added by name and removed with the trash icon.
Screenshots land in tests_e2e/screenshots (open them after a run).
"""
from __future__ import annotations

from pathlib import Path

import pytest

SHOTS = Path(__file__).parent / "screenshots"
PANEL = "/template-attributes"


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


@pytest.fixture
def helper(page, ha_base_url):
    """A fresh helper per test, removed afterwards."""
    page.goto(ha_base_url + "/")
    page.wait_for_load_state("networkidle")
    flow = _api(page, "POST", "/api/config/config_entries/flow", {"handler": "template_attributes"})
    result = _api(
        page,
        "POST",
        f"/api/config/config_entries/flow/{flow['flow_id']}",
        {"name": "E2E Demo", "state_template": "{{ 40 + 2 }}"},
    )
    assert result["type"] == "create_entry", result
    entry_id = result["result"]["entry_id"]
    yield entry_id
    _api(page, "DELETE", f"/api/config/config_entries/entry/{entry_id}")


def _open_panel(page):
    page.goto(PANEL)
    page.wait_for_selector("template-attributes-panel details")


def test_add_edit_save_and_delete_attributes(page, helper):
    _open_panel(page)
    SHOTS.mkdir(exist_ok=True)

    # the standard sensor is a collapsed section titled "<label> = <live state>"
    state = page.locator("details[data-section='__state__']")
    assert state.get_attribute("open") is None
    assert "42" in state.locator("summary").inner_text()

    # add an attribute by name; the new section opens for editing
    page.get_by_label("Name of the new attribute").fill("double")
    page.get_by_role("button", name="Add attribute").click()
    section = page.locator("details[data-section='double']")
    assert section.get_attribute("open") is not None
    section.locator("textarea").fill("{{ state * 2 }}")

    # a second one; the input row is below the list again
    page.get_by_label("Name of the new attribute").fill("note")
    page.get_by_role("button", name="Add attribute").click()
    page.locator("details[data-section='note'] textarea").fill("hello")
    page.screenshot(path=str(SHOTS / "panel-editing.png"))

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_selector("text=Saved.")

    # after saving everything is closed again and the titles show the live values
    # (Playwright selectors pierce shadow DOM; document.querySelector would not find the panel)
    page.wait_for_selector("[data-value='double']:text-is('84')")
    assert page.locator("details[open]").count() == 0
    assert "note" in page.locator("details[data-section='note'] summary").inner_text()
    assert "hello" in page.locator("details[data-section='note'] summary").inner_text()
    page.screenshot(path=str(SHOTS / "panel-overview.png"))

    # delete with the trash icon; saving removes the attribute from the entity
    page.get_by_label("Delete attribute: note").click()
    assert page.locator("details[data-section='note']").count() == 0
    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_selector("text=Saved.")
    page.reload()
    page.wait_for_selector("template-attributes-panel details")
    assert page.locator("details[data-section='note']").count() == 0
    assert page.locator("details[data-section='double']").count() == 1


def test_invalid_name_and_template_are_reported(page, helper):
    _open_panel(page)

    page.get_by_label("Name of the new attribute").fill("1bad")
    page.get_by_role("button", name="Add attribute").click()
    assert page.locator("text=Use letters, digits and underscore only").count() == 1

    page.get_by_label("Name of the new attribute").fill("broken")
    page.get_by_role("button", name="Add attribute").click()
    page.locator("details[data-section='broken'] textarea").fill("{{ 1 + ")
    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_selector("text=Template is not valid")
    # the section with the problem is opened so the message is visible
    assert page.locator("details[data-section='broken']").get_attribute("open") is not None
    page.screenshot(path=str(SHOTS / "panel-error.png"))


def _create_helper(page, name: str, state_template: str) -> str:
    flow = _api(page, "POST", "/api/config/config_entries/flow", {"handler": "template_attributes"})
    result = _api(
        page,
        "POST",
        f"/api/config/config_entries/flow/{flow['flow_id']}",
        {"name": name, "state_template": state_template},
    )
    assert result["type"] == "create_entry", result
    return result["result"]["entry_id"]


@pytest.fixture
def second_helper(page, helper):
    """A second helper, so that "the first one" and "the linked one" differ."""
    entry_id = _create_helper(page, "Zweiter Helfer", "{{ 7 }}")
    yield entry_id
    _api(page, "DELETE", f"/api/config/config_entries/entry/{entry_id}")


def test_options_dialog_link_opens_the_panel_with_that_helper(page, second_helper):
    """Click through the real UI: integration page -> Configure -> "Manage attributes" link."""
    SHOTS.mkdir(exist_ok=True)
    page.goto("/config/integrations/integration/template_attributes")
    row = page.locator("ha-integration-card, ha-config-entry-row").filter(has_text="Zweiter Helfer")
    row.get_by_role("button", name="Configure").click()

    link = page.get_by_role("link", name="Manage attributes")
    link.wait_for()
    page.screenshot(path=str(SHOTS / "options-dialog.png"))
    assert second_helper in link.get_attribute("href")
    link.click()

    # the panel opens with the helper of the dialog, not with the first one
    page.wait_for_selector("template-attributes-panel details")
    assert page.url.endswith(f"/template-attributes?entry={second_helper}")
    assert page.get_by_role("combobox", name="Helper").input_value() == second_helper
    assert "7" in page.locator("details[data-section='__state__'] summary").inner_text()
    page.screenshot(path=str(SHOTS / "panel-from-options-link.png"))


def test_deep_link_preselects_the_helper(page, helper):
    """The options dialog links to /template-attributes?entry=<id>: that helper must be shown."""
    second = _create_helper(page, "Zweiter Helfer", "{{ 7 }}")
    try:
        # without the parameter the first helper is shown, with it the linked one
        page.goto(f"{PANEL}?entry={second}")
        page.wait_for_selector("template-attributes-panel details")
        assert page.get_by_role("combobox", name="Helper").input_value() == second
        assert "7" in page.locator("details[data-section='__state__'] summary").inner_text()
        # an unknown id falls back instead of showing an empty panel
        page.goto(f"{PANEL}?entry=does-not-exist")
        page.wait_for_selector("template-attributes-panel details")
    finally:
        _api(page, "DELETE", f"/api/config/config_entries/entry/{second}")


def test_settings_link_points_to_the_integration(page, helper):
    _open_panel(page)
    href = page.get_by_role("link", name="Standard sensor settings").get_attribute("href")
    assert href == "/config/integrations/integration/template_attributes"
