# robotic_arm

Controls a Mecademic Meca500 robot arm for automated NMR sample handling. The module provides a high-level interface for picking, placing, and flipping sample tubes across named laboratory positions (facilities), built on top of the mecademicpy library.

---

## Files

| File | Purpose |
|------|---------|
| `roboarm.py` | Main `RobotArm` class — all automation logic |
| `facility.py` | `Facility` class and `load_facilities()` — named lab positions |
| `facility_config.json` | Physical coordinates for all lab positions |
| `cli_tool.py` | Keyboard-driven joystick for manual testing |
| `sounds.py` | Audio beep utilities |

---

## Coordinate System

The arm operates in a **hybrid cylindrical-Cartesian** system:

```
CartPos = (x, y, z, alpha, beta, gamma)
          mm  mm  mm  deg   deg   deg
```

Three simplified movement primitives map to cylindrical operations:

| Method | Cylindrical axis | Direction |
|--------|-----------------|-----------|
| `change_vertical_height(dist)` | Z (height) | positive = up |
| `change_radial_distance(dz)` | R (depth) | positive = away from carousel |
| `change_azimuth(theta)` | θ (rotation) | positive = clockwise |

The **carousel** is the imaginary circle (~200–250 mm radius) that the arm travels along between positions. The arm always retracts to the carousel perimeter before moving to a new facility.

```
  [shimming]  [dryer]
                                          [tube1]
  [spinsolve]      arm  ─────────────────[tube2]    [sample well plate]  ──── pipetter (XY)
                                                              │
  [waste]  [washer1]  [washer2]                         (reaction samples)
```

---

## Facilities

Facilities are named laboratory positions loaded from `facility_config.json`. Each facility has:
- **low position** — working height where the gripper engages the tube
- **high position** — safe transit height above equipment

| Facility | Purpose |
|----------|---------|
| `tube1` – `tube4` | Sample tube rack slots |
| `washer1`, `washer2` | Sequential tube washing stations |
| `dryer` | Tube drying station |
| `flip_stand_waste` | Flip stand near waste (invert tube) |
| `flip_stand_clean` | Flip stand near clean side (invert tube) |
| `spinsolve` | NMR spectrometer insertion point |
| `reference_slot` | Shimming reference sample slot |

---

## RobotArm Class

### Initialization

```python
from robotic_arm.roboarm import RobotArm

robot = RobotArm(running_vel="default", is_check_item_gripping=True)
```

Connects to the arm at `192.168.0.100`, loads facilities, and configures the gripper.

### Tube Status

The arm tracks the current tube state:

| Value | Meaning |
|-------|---------|
| `0` | No tube held |
| `1` | Tube held upright |
| `-1` | Tube held inverted |

Orientation constraints are enforced automatically — e.g. washer/dryer require an inverted tube, tube racks require upright.

### High-Level Methods

```python
# Pick a tube from a rack slot
robot.pick_tube(robot.facilities['tube1'])

# Place tube into a facility
robot.place_tube(robot.facilities['washer1'])

# Flip tube upside down using a flip stand
robot.flip_tube(location='flip_stand_waste')

# Insert tube into NMR spectrometer
robot.place_tube_to_spinsolve()

# Remove tube from NMR spectrometer
robot.pick_tube_from_spinsolve()

# Navigate to a facility (without pick/place)
robot.move_to(robot.facilities['dryer'])
```

### Navigation Methods

```python
robot.retract_to_carousel()          # Move to safe carousel perimeter
robot.go_to_high_z()                 # Raise to safe transit height
robot.go_to_high_location(target)    # Full transit to a target CartPos
```

### Movement Primitives

```python
robot.change_vertical_height(10)     # Move up 10 mm
robot.change_radial_distance(-5)     # Move 5 mm toward carousel center
robot.change_azimuth(15)             # Rotate 15° clockwise

robot.move_pose(x, y, z, a, b, g)   # Absolute cartesian move
robot.move_lin(x, y, z, a, b, g)    # Linear interpolated move
robot.move_joints(j1, j2, j3, j4, j5, j6)  # Joint-space move
```

### Gripper

```python
robot.change_gripper_state()         # Toggle open/close
robot.invert_gripper()               # Rotate 180° (flip orientation)
robot.is_gripper_gripping_item()     # True if force < -10 N
robot.get_gripper_force()            # Returns force in N
```

### Status

```python
robot.get_cart_pos()                 # Returns current (x,y,z,a,b,g)
robot.is_gripper_opened()
robot.is_gripper_inverted()
robot.is_tube_inverted()
robot.is_arm_at_carousel()
robot.is_located_at(loc_coord, coord_num)
```

---

## CLI Joystick (Manual Testing)

```bash
cd nmr-station/robotic_arm
python cli_tool.py joystick
```

| Key | Action |
|-----|--------|
| ↑ / ↓ | Move up / down |
| W / S | Extend / retract radially |
| A / D or ← / → | Rotate azimuth |
| G | Toggle gripper |
| [ / ] | Rotate selected joint |
| , / . | Decrease / increase step size |
| F1 | Reset robot |
| F12 | Move to zero position |
| Q | Quit |

---

## Configuration

**Connection:** Hardcoded to `192.168.0.100:10000`

**Position coordinates** are stored in `facility_config.json`:

```json
{
    "tube1": {
        "handle_tube": "pick_place_upright",
        "pos_low": [48.7, 212.8, 112, -90, 12.9, 90],
        "pos_high_z": 345
    }
}
```

**Motion constants** (HIGH\_Z, CAROUSEL\_RADIUS, SAFE\_POS, TUBE\_LENGTH) are loaded from the parent `settings/` module via environment variables.

---

## Safety Features

- **Force feedback** — grip verified with force sensor (< −10 N = secure)
- **Position tolerance** — movements verified to ±0.05 mm
- **Tube status tracking** — orientation mismatch raises an error before movement
- **Carousel transit** — arm always retracts to safe perimeter path between positions
- **Singularity avoidance** — `refresh_j4()` corrects near-zero joint angles
- **Manual confirmation** — `go_to_safe()` and `zero()` require explicit user confirmation
- **Exception logging** — all errors logged with context via `@log_exception`
