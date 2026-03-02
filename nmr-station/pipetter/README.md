# pipetter

Controls an automated liquid handling system for NMR sample preparation. The module combines a GRBL-driven XYZ gantry (miniPi) with a Hamilton Zeus LT pipetting instrument to aspirate reaction samples from a well plate and dispense them into NMR tubes.

---

## Files

| File | Purpose |
|------|---------|
| `pipetter.py` | Main `PipetterControl` class — full orchestration of motion + liquid handling |
| `breadboard.py` | Physical layout definitions — plate, tube rack, tip rack, coordinates |
| `__init__.py` | Exports `PipetterControl` |
| `grbl/` | GRBL CNC firmware source (runs on Arduino Uno, controls XYZ stage) |

**External config files** (paths from `.env`):

| File | Purpose |
|------|---------|
| `brb.json` | XY/Z coordinates for plate, tubes, tips, trash, idle positions |
| `tip_rack.json` | Per-tip availability tracking (updated live during operation) |
| `grbl_settings.txt` | GRBL motion parameters (speed, acceleration, steps/mm) |

---

## Hardware

| Device | Connection | Protocol |
|--------|-----------|----------|
| miniPi XYZ gantry (GRBL on Arduino Uno) | COM3, 115200 baud | G-code over serial |
| Hamilton Zeus LT pipetter | USB Serial Port (auto-detected), 19200 baud, EVEN parity | Proprietary binary commands |



---

## Classes

### `PipetterControl` — main class

```python
from pipetter import PipetterControl

pip = PipetterControl(re_config_grbl=False)
```

Connects to GRBL on COM3, auto-detects Zeus serial port, loads coordinates, homes XYZ axes.

#### High-level operations

```python
pip.aspirate(sample_id)      # Draw from one of 54 well plate vials (id 0–53)
pip.refill(tube_id)          # Dispense into one of 4 NMR tubes (id 0–3)
pip.standby()                # Move to traverse height → trash → init Zeus
```

#### Tip management

```python
pip.pick_tip()               # Find next available tip, pick it up, update tip_rack.json
pip.discard_tip()            # Move to trash and discard current tip
pip.change_tip()             # Discard current + pick new tip
pip.reload_tip_rack()        # Mark all 96 tips as available (after physical reload)
```

#### XY motion

```python
pip.move_xy((x, y))          # Move to absolute XY coordinates
pip.move_xy_rel((dx, dy))    # Relative XY move
pip.move_to_traverse_height()# Raise to safe Z before lateral movement
pip.move_to_trash_bin()      # Move to waste bin position
pip.move_to_idle_position()  # Move to standby position
pip.home()                   # Home all axes
```

#### Z motion (pipetter head height)

```python
pip.move_z(target_z)         # Absolute Z (negative = down, 0 = home)
pip.move_z_rel(distance)     # Relative Z move
```

#### Liquid handling (low-level)

```python
pip.draw_liquid(xy, asp_height, volume, n_retries=3)   # Aspirate with retry
pip.dispense_liquid(xy, disp_height)                    # Dispense at location
```

#### GRBL interface

```python
pip.send_to_xy_stage(command)   # Send raw G-code
pip.configure_grbl()            # Upload settings from grbl_settings.txt
pip.xy_pos()                    # Query current XY position
pip.kill_alarm()                # Override GRBL alarm state ($X)
```

---

### `Zeus` — Hamilton Zeus LT instrument

Handles all liquid operations: aspiration, dispensing, liquid level detection, tip management.

Key methods used by `PipetterControl`:

| Method | Purpose |
|--------|---------|
| `aspirate(volume, flow_rate, ...)` | Draw liquid into tip |
| `disp(flow_rate, ...)` | Release liquid from tip |
| `asp_blow_out_vol()` | Clear residual liquid before aspiration |
| `mixing_asp()` | Mix sample during aspiration |
| `asp_transport_air_volume()` | Draw air gap for transport |
| `tip_pick_up()` | Engage tip onto Zeus head |
| `tip_discard()` | Eject tip |
| `clld_start()` / `clld_stop()` | Capacitive liquid level detection |
| `re_error_code()` | Read last error (e.g. 75=no tip, 81=empty tube) |

---

### `breadboard.py` — layout definitions

Defines the physical geometry of all hardware on the deck:

| Object | Type | Description |
|--------|------|-------------|
| `plate0` | `Plate` | 54 sample vials (6 rows × 9 columns) |
| `tube_rack` | `Tube_rack` | 4 NMR collection tubes |
| `tip_rack` | dict | 96 tips loaded from `tip_rack.json` |
| `deckgeom_1000ul` | `Deck` | 1000 µl tip rack geometry (8×12) |

Well positions are interpolated from four corner coordinates defined in `brb.json`.

---

## Coordinate System

- All working coordinates are **negative** (GRBL home = 0,0,0; working area = negative XY, negative Z)
- Z = 0 at top (home); negative Z = downward into samples
- `ZeusTraversePosition` (default −30 mm) is the safe lateral transit height

```
Z = 0      ← home (top)
Z = -30    ← traverse height (safe for XY moves)
Z = -80    ← typical aspiration depth
Z = -150   ← floor (max Z travel)
```

---

## Tip Tracking

Tip availability is stored in `tip_rack.json`:

```json
{
  "1000ul": {
    "tips": [
      {"exists": true,  "xy": [-10.5, -20.3], "tipTypeTableIndex": 6, ...},
      {"exists": false, "xy": [-10.5, -27.8], ...},
      ...
    ]
  }
}
```

- `"exists": true` — tip is available
- `"exists": false` — tip has been used

The file is updated after every pick. When all 96 tips are used, the user is prompted to reload the rack and call `reload_tip_rack()`.

---

## Integration with Scheduler

`PipetterControl` is used by `PipetterDecision` in `scheduler.py`. The pipetter runs in its own thread and communicates via message queue:

| Message received | Action |
|-----------------|--------|
| `"NextSample?"` | Report next tube ID and sample ID |
| `"PauseRefill"` | Call `standby()`, reply `"PauseRefillOkay"` |
| `"ResumeRefill"` | Resume refilling loop |
| `"ReturnTube"` | Call `standby()`, reply `"ReadyToReturnTube"` |

The pipetter sends `"Terminate"` when all samples have been processed.

**Transfer volume:** 600 µl per sample (defined as `TRANSFER_VOLUME = 6000` in pipetter.py, in Zeus units).

---

## Configuration

All coordinates are in `brb.json` (path from `.env` → `PIPETTER_COORDINATES_FILE_PATH`):

```json
{
  "ZeusTraversePosition": -30,
  "floor_z": -150,
  "plate0": [[x,y], [x,y], [x,y], [x,y]],
  "tube1_xy": [x, y],  "tube1_height": z,
  "rack_1000ul": [[x,y], [x,y], [x,y], [x,y]],
  "trash_xy": [x, y],
  "idle_xy": [x, y]
}
```

Motion parameters are in `grbl_settings.txt` (uploaded once via `configure_grbl()`):

```
$110=500.000    (X max rate mm/min)
$120=10.000     (X acceleration mm/sec²)
...
```
