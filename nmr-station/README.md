# nmr-station

Hardware automation layer for the NMR robotic platform. Orchestrates three devices — a Mecademic Meca500 robot arm, a Hamilton Zeus LT liquid handler, and a Magritek Spinsolve 80 MHz spectrometer — across concurrent threads to autonomously transfer samples, acquire NMR spectra, and clean tubes with no manual intervention.

---

## Directory structure

```
nmr-station/
├── app.py                  # Flask web UI entry point
├── scheduler.py            # Direct-run entry point + all decision classes
├── sound.py                # Audio alert utilities
├── logger.py               # Logger setup helpers
├── liquid_level_sensor.py  # Liquid level sensor interface (standalone utility)
│
├── robotic_arm/            # Mecademic Meca500 control
├── pipetter/               # Hamilton Zeus LT + miniPi GRBL gantry control
├── spectrometer/           # Spinsolve 80 MHz XML remote-control client
├── shared_state/           # Thread-safe tube tracker and message queues
├── settings/               # .env loader and all runtime constants
├── templates/              # Jinja2 + HTMX templates for the Flask web UI
├── tests/                  # Dummy device implementations for offline testing
└── images/                 # UI image assets (button icons)
```

Each sub-module has its own `README.md` with detailed documentation.

---

## Entry points

### 1. Web UI mode — `app.py`

```bash
python nmr-station/app.py
```

Starts a Flask server at `http://localhost:5000`. Use the browser UI to:

1. Set the instrument user record (Solvent, Sample, Custom field)
2. Enter the vial IDs to process (e.g. `1,2,3`)
3. Select and configure one or more acquisition protocols
4. Click **Start Automation** to launch the scheduler

Protocols available in the web UI: `1D PROTON`, `1D EXTENDED+`, `1D WET SUP`.

### 2. Direct / GUI mode — `scheduler.py`

```bash
python nmr-station/scheduler.py
```

Shows a **pre-flight checklist** GUI (PySimpleGUI), then opens a **measurement info** dialog to collect:

| Field | Description |
|-------|-------------|
| Reaction Name | Label for this experiment |
| User Name | Operator initials |
| Well Plate Number | Plate identifier for the log file |
| Reaction Solvent | Solvent name (recorded in log) |
| Reaction Excel Path | `.xlsx` file with `uuid` and `container_id` columns |
| Vials to Measure | Range/list syntax, e.g. `0-5, 7, 10-12` |

Last-entered values are saved to `MEASUREMENT_DATA_GUI_PATH` and pre-filled on the next run.

---

## Pre-flight checklist

Before each run in direct mode, the operator must tick all items:

1. Disable WiFi and disconnect router
2. Open Spinsolve software
3. Specify storage directory in Spinsolve
4. Make well plate ready
5. Check/refill pipetting tips and reload `breadboard.py`
6. Make two NMR tubes ready
7. Turn on air pressure
8. Turn on vacuum
9. Check/refill cleaning solvent
10. Empty waste bottle
11. Check reference sample (for shimming)
12. Turn on heat guns (tube dryer)

Submission is blocked if any item is unchecked.

---

## Architecture — three concurrent threads

```
┌─────────────────────────────────────────────────────────────┐
│                        Scheduler                            │
│                                                             │
│  PipetterDecision   RobotArmDecision   NMR_Spectrometer     │
│       thread    ◄──── producer_mq ────►    Decision         │
│                         SharedState         thread          │
│                            │                    │           │
│                      consumer_mq ───────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### `Scheduler`

Dependency-injects the three decision objects and runs each in its own `threading.Thread`. Blocks until all threads finish.

### `RobotArmDecision` — robot arm thread

Runs a priority loop every 0.5 s:

| Priority | Action |
|----------|--------|
| 0 (highest) | Periodic shimming — insert reference sample every `MAX_SAMPLE_COUNT_AFTER_SHIMMING` samples (default: 5) |
| 1 | Eject analyzed tube from spectrometer → flip into waste collector (`DitchSample`) |
| 2 | Load next filled tube from rack into spectrometer, notify spectrometer (`NewSampleReady`) |
| 3 | Progress tubes through the cleaning pipeline: waste_collector → washer1 → washer2 → dryer → tube rack |
| 4 (lowest) | Detect `Terminate` from pipetter and propagate to spectrometer thread |

Tube cleaning waits are timer-based using `time_finished` set from `settings/`:

| Stage | Default duration |
|-------|----------------|
| Waste collector (emptying) | 15 s |
| Washer 1 | 45 s |
| Washer 2 | 45 s |
| Dryer | 120 s |
| Cooling after dryer | 30 s |

### `NMR_SpectrometerDecision` — spectrometer thread

Listens on `consumer_message_queue`:

| Message received | Action |
|-----------------|--------|
| `NewSampleReady` | Sets sample ID in Spinsolve via XML `Set`, runs the configured acquisition sequence, logs result to CSV |
| `ShimReference` | Runs `SHIM QuickShim1st2nd` on the reference sample, replies `RemoveReference` |
| `Terminate` | Exits thread |

Per-sample measurement info (start/end time, data folder, reaction UUID) is appended to a CSV log at `ROBOT_ARM_LOG_PATH/measurement_log/<excel_name>_plate_<plate_number>.csv`.

### `PipetterDecision` — pipetter thread

Continuously fills empty NMR tubes from the well plate in `process_order` sequence. Responds to robot arm requests on `producer_message_queue`:

| Message received | Action |
|-----------------|--------|
| `NextSample?` | Reply with `TubeId=X` for the next filled tube |
| `PauseRefill` | Call `standby()`, reply `PauseRefillOkay` |
| `ResumeRefill` | Resume filling loop |
| `ReturnTube` | Call `standby()`, reply `ReadyToReturnTube` |

Sends `Terminate` when the process order is exhausted and all tubes are empty.

---

## Configuration — `settings/`

All settings are loaded from `settings/.env` via `python-dotenv`. Edit this file to configure hardware connections and file paths.

| Variable | Description |
|----------|-------------|
| `ROBOT_ARM_HOST` | Robot arm IP (default `192.168.0.100`) |
| `ROBOT_ARM_LOG_PATH` | Directory for scheduler and measurement logs |
| `SPECTROMETER_REMOTE_CONTROL_HOST` | Spinsolve host (default `127.0.0.1`) |
| `SPECTROMETER_REMOTE_CONTROL_PORT` | Spinsolve port (default `13000`) |
| `MEASUREMENT_DATA_GUI_PATH` | JSON file path for persisting GUI form values |
| `PIPETTER_LOG_PATH` | Directory for pipetter logs |
| `PIPETTER_TIP_RACK_FILE_PATH` | Path to `tip_rack.json` |
| `PIPETTER_COORDINATES_FILE_PATH` | Path to `brb.json` (deck coordinates) |
| `PIPETTER_GRBL_SETTINGS_FILE_PATH` | Path to `grbl_settings.txt` |

Numeric constants in `settings/loader.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `TUBE_COUNT` | 2 | Number of NMR tubes in the rack |
| `MAX_SAMPLE_COUNT_AFTER_SHIMMING` | 5 | Samples between re-shims |
| `HIGH_Z` | 340 mm | Robot arm safe transit height |
| `CAROUSEL_RADIUS` | 25 mm | Robot arm carousel retract radius |
| `TUBE_LENGTH` | 275 mm | NMR tube length |
| `REMOTE_CONTROL_TIMEOUT` | 10 s | Spinsolve TCP socket timeout |

---

## Logging

`scheduler.py` writes to `ROBOT_ARM_LOG_PATH/Scheduler.log` (INFO level) and prints WARNING+ to the console with ANSI colour formatting.

Per-sample measurement records are written as CSV rows to:
```
ROBOT_ARM_LOG_PATH/measurement_log/<reaction_excel_name>_plate_<plate_number>.csv
```

Columns: `reaction_name`, `user_name`, `well_plate_number`, `reaction_solvent`, `reaction_excel_path`, `sample_well_id`, `measurement_start_time`, `measurement_end_time`, `data_folder`, `reaction_uuid`.

---

## Testing without hardware

Swap real device classes for their dummies at the top of `scheduler.py`:

```python
from tests.dummy_robotarm   import DummyRobotArmControl   as RobotArm
from tests.dummy_pipetter   import DummyPipetterControl   as PipetterControl
from tests.dummy_spectrometer import DummySpectrometerRemoteControl as SpectrometerRemoteControl
```

All three dummies implement the same interface as the real classes but print actions to stdout instead of communicating with hardware.

---

## Sub-module documentation

| Module | README |
|--------|--------|
| `robotic_arm/` | [robotic_arm/README.md](robotic_arm/README.md) |
| `pipetter/` | [pipetter/README.md](pipetter/README.md) |
| `spectrometer/` | [spectrometer/README.md](spectrometer/README.md) |
| `shared_state/` | [shared_state/README.md](shared_state/README.md) |
| `templates/` | [templates/README.md](templates/README.md) |
