# Template Attributes

Home Assistant custom integration (`custom_components/template_attributes`), distributed via HACS.
Sister project of `ha-template-forecast` (same conventions).

## Rules

- **Docs are bilingual.** README, `examples/`, and other user-facing docs are always updated in
  German and English in the same change. Root README: English first, German section at the end.
  Examples: `examples/en/` and `examples/de/`. Exceptions: the README developer section and
  `docs/REQUIREMENTS.md` (German only).
- **`docs/REQUIREMENTS.md` is the spec.** Read it before behavior changes; update it together
  with the code. Keep functional requirements (what) separate from technical aspects (how).
- **Conventional Commits** (`feat`, `fix`, `docs`, `chore`, `ci`, `test`; `feat!` for breaking).
  They drive semantic-release. Never hand-edit the version, `CHANGELOG.md`, or make
  `chore(release)` commits - CI does that. Do not commit/push unless asked.
- **Tests:** run `python -m pytest` (never bare `pytest`) in the devcontainer. Changes to the
  config/options flow also need a case in `tests_e2e/` (real browser); run with
  `pip install -r requirements_e2e.txt`, `python -m playwright install --with-deps chromium`,
  `python -m pytest tests_e2e`, then **open the screenshots** in `tests_e2e/screenshots/`.
- **Translations:** `strings.json`, `translations/en.json`, `translations/de.json` stay in sync.
  They are ICU MessageFormat - escape literal `{`/`}` with `'...'` quoting, not doubling; avoid
  single apostrophes in texts with placeholders. The labels of the fields inside an attribute section
  (dynamic keys, not translatable) live in `SECTION_LABELS` in `config_flow.py`.
- **Robustness:** errors in user-supplied templates are validated with localized messages and must
  never crash the integration or HA.
- Pinned `homeassistant` version dictates the minimum Python version (CI + devcontainer).

## Layout

- `custom_components/template_attributes/` - integration: `config_flow.py` (create flow, options flow
  with one section per attribute, shared attribute step), `sensor.py`, `validation.py`. There is no
  frontend code: everything runs in the standard HA dialogs.
- `tests/` - mocked unit/flow tests; `tests_e2e/` - real HA + Playwright
- `docs/REQUIREMENTS.md` - requirements spec
- `examples/{en,de}/` - documented examples
- `.github/` - workflows (test, test-e2e, release with test gate), PR template (bilingual)
