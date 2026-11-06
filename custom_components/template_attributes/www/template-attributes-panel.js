/*
 * Template Attributes - editor panel (plain JS, no build step).
 *
 * One collapsed section per definition. The section title shows the name and the *live* value
 * of the attribute (read from the entity's state, so it follows the template by itself).
 * Talks to the integration only through the websocket commands template_attributes/list|save.
 */
const NAME_RE = /^[A-Za-z_][A-Za-z0-9_]*$/;
const RESERVED = [
  "friendly_name", "unit_of_measurement", "device_class", "state_class", "icon",
  "entity_picture", "supported_features", "attribution", "assumed_state", "restored",
  "editable", "id", "entity_id",
];
const TRASH =
  "M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z";

const TEXTS = {
  en: {
    title: "Template Attributes",
    helper: "Helper",
    none: "No Template Attributes helper exists yet.",
    create: "Create one under Settings → Devices & services → Helpers.",
    stateSection: "State",
    stateHint: "Template for the state of the sensor.",
    attrHint: "Template for the attribute. Use {{ state }} for the state of this sensor.",
    addPlaceholder: "Name of the new attribute",
    add: "Add attribute",
    save: "Save",
    discard: "Discard changes",
    saved: "Saved.",
    remove: "Delete attribute",
    settings: "Standard sensor settings",
    unsaved: "Unsaved changes",
    loadError: "Could not load the helpers.",
    saveError: "Could not save.",
    invalid_attribute_name: "Use letters, digits and underscore only; do not start with a digit.",
    reserved_attribute_name: "This name is reserved by Home Assistant.",
    duplicate_attribute_name: "This name is already used.",
    invalid_template: "Template is not valid",
    template_render_error: "Template failed on a test render",
  },
  de: {
    title: "Template Attributes",
    helper: "Helfer",
    none: "Es gibt noch keinen Template-Attributes-Helfer.",
    create: "Lege einen unter Einstellungen → Geräte & Dienste → Helfer an.",
    stateSection: "Zustand",
    stateHint: "Template für den Zustand des Sensors.",
    attrHint: "Template für das Attribut. Mit {{ state }} ist der Zustand dieses Sensors verfügbar.",
    addPlaceholder: "Name des neuen Attributs",
    add: "Attribut hinzufügen",
    save: "Speichern",
    discard: "Änderungen verwerfen",
    saved: "Gespeichert.",
    remove: "Attribut löschen",
    settings: "Einstellungen des Standard-Sensors",
    unsaved: "Ungespeicherte Änderungen",
    loadError: "Die Helfer konnten nicht geladen werden.",
    saveError: "Speichern fehlgeschlagen.",
    invalid_attribute_name: "Nur Buchstaben, Ziffern und Unterstrich; nicht mit einer Ziffer beginnen.",
    reserved_attribute_name: "Dieser Name ist von Home Assistant reserviert.",
    duplicate_attribute_name: "Dieser Name wird bereits verwendet.",
    invalid_template: "Template ist ungültig",
    template_render_error: "Template ist beim Testrendern fehlgeschlagen",
  },
};

const STYLE = `
  :host { display: block; background: var(--primary-background-color); color: var(--primary-text-color);
          min-height: 100%; font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
  header { display: flex; align-items: center; gap: 12px; padding: 0 16px; height: 56px; box-sizing: border-box;
           background: var(--app-header-background-color, var(--primary-color)); color: var(--app-header-text-color, #fff); }
  header button.menu { background: none; border: 0; color: inherit; font-size: 24px; cursor: pointer; display: none; }
  :host([narrow]) header button.menu { display: block; }
  header h1 { font-size: 20px; font-weight: 400; margin: 0; flex: 1; }
  main { max-width: 900px; margin: 0 auto; padding: 16px; }
  .toolbar { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-bottom: 16px; }
  .toolbar a { color: var(--primary-color); }
  select, input, textarea { font: inherit; color: inherit; background: var(--card-background-color, #fff);
           border: 1px solid var(--divider-color); border-radius: 4px; padding: 8px; box-sizing: border-box; }
  details { background: var(--card-background-color, #fff); border: 1px solid var(--divider-color);
            border-radius: 8px; margin-bottom: 8px; }
  summary { display: flex; align-items: center; gap: 8px; padding: 12px 16px; cursor: pointer; list-style: none; }
  summary::-webkit-details-marker { display: none; }
  summary::before { content: "▸"; color: var(--secondary-text-color); }
  details[open] > summary::before { content: "▾"; }
  .label { font-weight: 500; }
  .eq { color: var(--secondary-text-color); }
  .value { color: var(--secondary-text-color); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .badge { font-size: 12px; color: var(--warning-color, #b26a00); }
  button.trash { background: none; border: 0; cursor: pointer; color: var(--secondary-text-color); padding: 4px; display: flex; }
  button.trash:hover { color: var(--error-color, #db4437); }
  button.trash svg { width: 20px; height: 20px; fill: currentColor; }
  .body { padding: 0 16px 16px; }
  .hint { color: var(--secondary-text-color); font-size: 13px; margin: 0 0 8px; }
  textarea { width: 100%; min-height: 80px; font-family: var(--code-font-family, monospace); resize: vertical; }
  .error { color: var(--error-color, #db4437); font-size: 13px; margin-top: 6px; white-space: pre-wrap; }
  .add { display: flex; gap: 8px; margin: 16px 0; align-items: flex-start; flex-wrap: wrap; }
  .add input { flex: 1; min-width: 200px; }
  button.btn { background: var(--primary-color); color: var(--text-primary-color, #fff); border: 0; border-radius: 4px;
               padding: 9px 16px; font: inherit; cursor: pointer; }
  button.btn.secondary { background: none; color: var(--primary-color); }
  button.btn:disabled { opacity: .45; cursor: default; }
  .actions { display: flex; gap: 8px; align-items: center; margin-top: 24px; }
  .banner { padding: 8px 12px; border-radius: 4px; margin-bottom: 12px; }
  .banner.ok { background: var(--success-color, #43a047); color: #fff; }
  .banner.err { background: var(--error-color, #db4437); color: #fff; }
`;

function formatValue(value) {
  if (value === undefined) return "—";
  if (value !== null && typeof value === "object") return JSON.stringify(value);
  return String(value);
}

class TemplateAttributesPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._helpers = null;
    this._selected = null;
    this._draft = null;
    this._dirty = false;
    this._errors = {};
    this._addError = "";
    this._message = null;
    this._loadError = false;
  }

  set hass(hass) {
    const first = !this._hass;
    this._hass = hass;
    if (first) this._load();
    else this._updateValues();
  }

  set narrow(value) { this.toggleAttribute("narrow", !!value); }
  set panel(_value) {}
  set route(_value) {}

  get _t() { return TEXTS[(this._hass?.language || "en").slice(0, 2)] || TEXTS.en; }

  async _load(keepSelection = true) {
    try {
      this._helpers = await this._hass.callWS({ type: "template_attributes/list" });
      this._loadError = false;
    } catch (err) {
      this._helpers = [];
      this._loadError = true;
    }
    const known = this._helpers.find((h) => h.entry_id === this._selected);
    if (!keepSelection || !known) this._selected = this._helpers[0]?.entry_id ?? null;
    this._resetDraft();
    this._render();
  }

  _helper() { return this._helpers?.find((h) => h.entry_id === this._selected); }

  _resetDraft() {
    const helper = this._helper();
    this._dirty = false;
    this._errors = {};
    this._addError = "";
    this._draft = helper && {
      state_template: helper.state_template,
      // every section starts closed: the overview of names and values is the point
      attributes: helper.attributes.map((a) => ({ name: a.name, template: a.template, open: false })),
    };
  }

  _liveState() {
    const entityId = this._helper()?.entity_id;
    return entityId ? this._hass.states[entityId] : undefined;
  }

  _updateValues() {
    if (!this._draft) return;
    const state = this._liveState();
    const stateEl = this.shadowRoot.querySelector('[data-value="__state__"]');
    if (stateEl) stateEl.textContent = state ? state.state : "—";
    this._draft.attributes.forEach((attr) => {
      const el = this.shadowRoot.querySelector(`[data-value="${attr.name}"]`);
      if (el) el.textContent = formatValue(state?.attributes[attr.name]);
    });
  }

  _error(err) {
    if (!err) return "";
    const text = this._t[err.code] || err.code;
    return err.message ? `${text}:\n${err.message}` : text;
  }

  _render() {
    const t = this._t;
    const root = this.shadowRoot;
    root.innerHTML = "";
    const style = document.createElement("style");
    style.textContent = STYLE;
    root.append(style);

    const header = document.createElement("header");
    const menu = document.createElement("button");
    menu.className = "menu";
    menu.textContent = "☰";
    menu.addEventListener("click", () =>
      this.dispatchEvent(new CustomEvent("hass-toggle-menu", { bubbles: true, composed: true })));
    const h1 = document.createElement("h1");
    h1.textContent = t.title;
    header.append(menu, h1);
    root.append(header);

    const main = document.createElement("main");
    root.append(main);

    if (this._loadError) return this._banner(main, "err", t.loadError);
    if (!this._helpers) return;
    if (!this._helpers.length) {
      const p = document.createElement("p");
      p.textContent = `${t.none} ${t.create}`;
      main.append(p);
      return;
    }

    this._renderToolbar(main);
    if (this._message) this._banner(main, this._message.kind, this._message.text);
    if (this._errors.general) this._banner(main, "err", this._errors.general);

    const state = this._liveState();
    main.append(this._section({
      key: "__state__", label: t.stateSection, value: state ? state.state : "—",
      hint: t.stateHint, template: this._draft.state_template, open: !!this._errors.state_template,
      error: this._errors.state_template, onInput: (v) => this._edit(() => { this._draft.state_template = v; }),
    }));

    this._draft.attributes.forEach((attr, index) => {
      const error = this._errors.attributes?.[attr.name];
      main.append(this._section({
        key: attr.name, label: attr.name, value: formatValue(state?.attributes[attr.name]),
        hint: t.attrHint, template: attr.template, open: attr.open || !!error, error,
        unsaved: attr.isNew,
        onToggle: (open) => { attr.open = open; },
        onInput: (v) => this._edit(() => { attr.template = v; }),
        onRemove: () => this._edit(() => { this._draft.attributes.splice(index, 1); }, true),
      }));
    });

    main.append(this._renderAddRow());
    main.append(this._renderActions());
    if (this._focusNew) this._focusNew();
    this._focusNew = null;
  }

  _renderToolbar(main) {
    const t = this._t;
    const bar = document.createElement("div");
    bar.className = "toolbar";
    if (this._helpers.length > 1) {
      const select = document.createElement("select");
      select.setAttribute("aria-label", t.helper);
      this._helpers.forEach((h) => {
        const opt = document.createElement("option");
        opt.value = h.entry_id;
        opt.textContent = h.title;
        opt.selected = h.entry_id === this._selected;
        select.append(opt);
      });
      select.addEventListener("change", () => {
        this._selected = select.value;
        this._message = null;
        this._resetDraft();
        this._render();
      });
      bar.append(select);
    } else {
      const strong = document.createElement("strong");
      strong.textContent = this._helper().title;
      bar.append(strong);
    }
    const link = document.createElement("a");
    link.href = "/config/integrations/integration/template_attributes";
    link.textContent = t.settings;
    bar.append(link);
    main.append(bar);
  }

  _banner(main, kind, text) {
    const div = document.createElement("div");
    div.className = `banner ${kind}`;
    div.textContent = text;
    main.append(div);
  }

  _section({ key, label, value, hint, template, open, error, unsaved, onToggle, onInput, onRemove }) {
    const details = document.createElement("details");
    details.dataset.section = key;
    details.open = open;
    if (onToggle) details.addEventListener("toggle", () => onToggle(details.open));

    const summary = document.createElement("summary");
    const name = document.createElement("span");
    name.className = "label";
    name.textContent = label;
    const eq = document.createElement("span");
    eq.className = "eq";
    eq.textContent = "=";
    const val = document.createElement("span");
    val.className = "value";
    val.dataset.value = key;
    val.textContent = value;
    summary.append(name, eq, val);
    if (unsaved) {
      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = this._t.unsaved;
      summary.append(badge);
    }
    if (onRemove) {
      const trash = document.createElement("button");
      trash.className = "trash";
      trash.title = this._t.remove;
      trash.setAttribute("aria-label", `${this._t.remove}: ${label}`);
      trash.innerHTML = `<svg viewBox="0 0 24 24"><path d="${TRASH}"/></svg>`;
      trash.addEventListener("click", (ev) => { ev.preventDefault(); ev.stopPropagation(); onRemove(); });
      summary.append(trash);
    }
    details.append(summary);

    const body = document.createElement("div");
    body.className = "body";
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = hint;
    const area = document.createElement("textarea");
    area.value = template;
    area.spellcheck = false;
    area.setAttribute("aria-label", label);
    area.addEventListener("input", () => onInput(area.value));
    body.append(p, area);
    if (error) {
      const err = document.createElement("div");
      err.className = "error";
      err.textContent = this._error(error);
      body.append(err);
    }
    details.append(body);
    return details;
  }

  _renderAddRow() {
    const t = this._t;
    const wrap = document.createElement("div");
    const row = document.createElement("div");
    row.className = "add";
    const input = document.createElement("input");
    input.placeholder = t.addPlaceholder;
    input.setAttribute("aria-label", t.addPlaceholder);
    const button = document.createElement("button");
    button.className = "btn";
    button.textContent = t.add;
    const add = () => this._addAttribute(input.value.trim());
    button.addEventListener("click", add);
    input.addEventListener("keydown", (ev) => { if (ev.key === "Enter") add(); });
    row.append(input, button);
    wrap.append(row);
    if (this._addError) {
      const err = document.createElement("div");
      err.className = "error";
      err.textContent = this._addError;
      wrap.append(err);
    }
    return wrap;
  }

  _renderActions() {
    const t = this._t;
    const actions = document.createElement("div");
    actions.className = "actions";
    const save = document.createElement("button");
    save.className = "btn";
    save.textContent = t.save;
    save.disabled = !this._dirty;
    save.dataset.action = "save";
    save.addEventListener("click", () => this._save());
    const discard = document.createElement("button");
    discard.className = "btn secondary";
    discard.textContent = t.discard;
    discard.disabled = !this._dirty;
    discard.dataset.action = "discard";
    discard.addEventListener("click", () => { this._message = null; this._resetDraft(); this._render(); });
    actions.append(save, discard);
    return actions;
  }

  /** Apply a draft change; rebuild only when the structure changed so typing keeps its focus. */
  _edit(change, rebuild = false) {
    change();
    this._message = null;
    this._dirty = true;
    if (rebuild) return this._render();
    // no rebuild while typing (it would drop the focus) - only enable the buttons
    this.shadowRoot.querySelectorAll("[data-action]").forEach((b) => { b.disabled = false; });
  }

  _addAttribute(name) {
    const t = this._t;
    if (!NAME_RE.test(name)) this._addError = t.invalid_attribute_name;
    else if (RESERVED.includes(name)) this._addError = t.reserved_attribute_name;
    else if (this._draft.attributes.some((a) => a.name === name)) this._addError = t.duplicate_attribute_name;
    else this._addError = "";
    if (this._addError) return this._render();

    this._draft.attributes.push({ name, template: "", open: true, isNew: true });
    this._focusNew = () =>
      this.shadowRoot.querySelector(`details[data-section="${name}"] textarea`)?.focus();
    this._edit(() => {}, true);
  }

  async _save() {
    const t = this._t;
    let result;
    try {
      result = await this._hass.callWS({
        type: "template_attributes/save",
        entry_id: this._selected,
        state_template: this._draft.state_template,
        attributes: this._draft.attributes.map((a) => ({ name: a.name, template: a.template })),
      });
    } catch (err) {
      this._errors = { general: `${t.saveError} ${err.message || ""}`.trim() };
      return this._render();
    }
    if (!result.ok) {
      this._errors = result.errors;
      this._message = null;
      return this._render();
    }
    this._message = { kind: "ok", text: t.saved };
    await this._load(true);
  }
}

customElements.define("template-attributes-panel", TemplateAttributesPanel);
