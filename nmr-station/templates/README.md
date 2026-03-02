# templates

Jinja2 HTML templates for the Flask web UI (`app.py`) and the Spinsolve XML schema reference. The UI is built with [HTMX](https://htmx.org/) — partial HTML fragments are swapped into the page on user interaction without full page reloads.

---

## Files

| File | Purpose |
|------|---------|
| `index.html.j2` | Full-page layout — user record form, sample order input, protocol builder, start button |
| `protocol_selection.html.j2` | Protocol dropdown partial — rendered when the user clicks "Add new protocol" |
| `protocol_param.html.j2` | Protocol parameter form partial — rendered when a protocol is selected from the dropdown |
| `protocol_mode_param.html.j2` | Mode-specific parameter partial — rendered when the `Mode` selector changes |
| `protocol_params_with_mode.html.j2` | Alternative combined mode+params partial (older variant) |
| `protocol_perform_list.html.j2` | Planned-protocol list partial — shows queued protocols with a Delete button per entry |
| `ProtocolOptions.xml` | Full list of Spinsolve protocols and their configurable options, parsed by `load_protocols()` |
| `RemoteControl.xsd` | Official Magritek XML schema for the Spinsolve remote-control protocol (reference only) |

---

## Web UI flow

```
GET /                      → index.html.j2 (full page)
                                │
                    ┌───────────┼────────────────────┐
                    ▼           ▼                     ▼
            User record    Sample order         Protocol builder
            (Solvent,      (vial IDs,           ─────────────────
             Sample,        e.g. 1,2,3)         Select protocol
             Custom)            │                     │
                │               │            GET /get_protocol_param
         POST /save-        POST /save-              │
          user-record        process-order    protocol_param.html.j2
                                              (params + Mode selector)
                                                      │
                                             GET /select_protocol_mode
                                                      │
                                             protocol_mode_param.html.j2
                                             (mode-specific fields only)
                                                      │
                                              POST /add_protocol
                                                      │
                                             protocol_perform_list.html.j2
                                             (list of queued protocols)
                                                      │
                                             GET /start_automation
                                             (launches Scheduler)
```

---

## Template details

### `index.html.j2` — main page

Rendered by `GET /`. Contains four `<div class="container">` sections:

| Section | id | Purpose |
|---------|----|---------|
| User record | `#user-record` | Set Solvent, Sample, Custom fields on the spectrometer via `POST /save-user-record` |
| Sample config | `#sample-config` | Enter comma-separated vial IDs to process via `POST /save-process-order` |
| Protocol config | `#protocol-config` | Build an ordered list of acquisition protocols |
| Start | `#start-automation` | Launch the scheduler via `GET /start_automation` |

Jinja2 variable: `protocols` — list of available protocol names shown in the dropdown.

---

### `protocol_param.html.j2` — parameter form

Rendered by `GET /get_protocol_param?protocol=<name>&Mode=<mode>`. Swapped into all `div.get_protocol_param` elements via `hx-swap-oob`.

Contains three out-of-band swap targets:

| `div` id | Content |
|----------|---------|
| `#protocol-mode-selection` | `Mode` dropdown (only if protocol has a `Mode` option) |
| `#protocol-mode-param` | Mode-dependent fields (e.g. saturation frequencies or auto ranges) |
| `#protocol-nonmode-param` | All other protocol parameters (inputs or selects) |
| `#add-protocol` | Submit button → `POST /add_protocol` |

Parameters with `"type": "input"` render as `<input type="text">`. Parameters with `"type": "select"` render as `<select>` with the allowed values from `ProtocolOptions.xml`.

---

### `protocol_mode_param.html.j2` — mode-specific fields

Rendered by `GET /select_protocol_mode?Mode=<mode>`. Swapped into `#protocol-mode-param`.

Shows only the fields relevant to the chosen `Mode`:

| Mode | Fields shown |
|------|-------------|
| `Auto` | `autoStart`, `autoEnd` |
| `Auto 2 Peaks` | `autoStart`, `autoEnd`, `autoStart2`, `autoEnd2` |
| `Auto 3 Peaks` | `autoStart`, `autoEnd`, `autoStart2`, `autoEnd2`, `autoStart3`, `autoEnd3` |
| `Manual` | `satFrequency1`, `satFrequency2`, `satFrequency3` |

---

### `protocol_perform_list.html.j2` — queue list

Rendered by `POST /add_protocol` and `DELETE /protocol-item/<id>`. Replaces `#protocol-list`.

Shows the ordered list of protocols queued for this run. Each entry has a Delete button that calls `DELETE /protocol-item/<id>` and re-renders the list. An "Add new protocol" button reloads the protocol selector partial.

---

### `protocol_selection.html.j2` — protocol dropdown partial

Rendered by `GET /get_protocol_selection`. Swapped into `#protocol-config` when the user clicks "Add new protocol" after viewing the perform list.

---

## ProtocolOptions.xml

A snapshot of all protocols and options supported by the connected Spinsolve unit. Parsed at startup by `load_protocols()` in `spectrometer/xml_converter.py`.

Structure:

```xml
<Script>
  <ProtocolOptions>
    <Protocol protocol="1D EXTENDED+">
      <Option name="Number">
        <Value>1</Value>
        <Value>2</Value>
        ...
      </Option>
      <Option name="AcquisitionTime">
        <Value />    <!-- empty Value → free-text input -->
      </Option>
      ...
    </Protocol>
    ...
  </ProtocolOptions>
</Script>
```

- An `<Option>` with non-empty `<Value>` elements → rendered as a `<select>` in the UI
- An `<Option>` with an empty `<Value />` → rendered as a free-text `<input>`

The available protocols shown in the web UI are filtered down to the three used in practice:

```python
available_protocols = ["1D PROTON", "1D EXTENDED+", "1D WET SUP"]
```

---

## RemoteControl.xsd

Official Magritek XML Schema Definition for the Spinsolve remote-control TCP/IP protocol. Documents all valid message types:

| Message type | Direction | Purpose |
|-------------|-----------|---------|
| `Set` | client → spectrometer | Set instrument fields (Solvent, Sample, DataFolder, …) |
| `Start` | client → spectrometer | Start an acquisition protocol |
| `Abort` | client → spectrometer | Abort current acquisition |
| `GetRequest` / `GetResponse` | client ↔ spectrometer | Query an instrument field |
| `AvailableProtocolsRequest/Response` | client ↔ spectrometer | List available protocols |
| `AvailableOptionsRequest/Response` | client ↔ spectrometer | List options for a protocol |
| `EstimateDurationRequest/Response` | client ↔ spectrometer | Estimate acquisition time |
| `HardwareRequest/Response` | client ↔ spectrometer | Query hardware status |
| `StatusNotification` | spectrometer → client | Push status updates during acquisition |

This file is for reference only — it is not loaded at runtime.
