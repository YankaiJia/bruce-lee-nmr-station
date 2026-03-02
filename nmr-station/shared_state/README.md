# shared_state

Thread-safe shared state for the NMR station scheduler. Provides two inter-thread communication primitives — a tube state tracker and two message queues — used by the robot arm, pipetter, and spectrometer threads to coordinate sample handoffs.

---

## Files

| File | Purpose |
|------|---------|
| `shared_state.py` | `SharedState` container — holds `TubeManager` and two `MessageQueue` instances |
| `tube_manager.py` | `TubeManager` — tracks the status and sample contents of each NMR tube |
| `message_queue.py` | `MessageQueue` — thread-safe FIFO queue for inter-thread messaging |
| `__init__.py` | Exports `SharedState` |

---

## Overview

The scheduler runs three concurrent threads:

```
pipetter thread  ──► producer_message_queue ──► robot arm thread
                                                      │
spectrometer thread ◄── consumer_message_queue ◄──────┘
```

All threads share a single `SharedState` instance. The tube manager records where each tube currently is (e.g. being filled, in the spectrometer, washing). The message queues carry handshake strings that coordinate physical tube transfers.

---

## SharedState

```python
from shared_state import SharedState

state = SharedState()
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `state.tube` | `TubeManager` | Status of all NMR tubes |
| `state.producer_message_queue` | `MessageQueue` | Pipetter ↔ robot arm channel |
| `state.consumer_message_queue` | `MessageQueue` | Robot arm ↔ spectrometer channel |
| `state.lock` | `threading.Lock` | Global lock for cross-attribute consistency |

The number of tubes is set by `TUBE_COUNT` from `settings/`.

---

## TubeManager

Tracks state for each of the `TUBE_COUNT` NMR tubes. All methods are thread-safe via an internal lock.

### Tube states

A tube progresses through the following states during a measurement cycle:

```
empty ──► filled ──► transferring ──► spectrometer ──► analyzing
                                                           │
dryer ◄── washer2 ◄── washer1 ◄── waste_collector ◄────────┘
  │
  └──► empty
```

| State | Meaning |
|-------|---------|
| `"empty"` | Tube is clean and available |
| `"filled"` | Sample has been dispensed into the tube by the pipetter |
| `"transferring"` | Robot arm is carrying the tube to the spectrometer |
| `"spectrometer"` | Tube is inserted into the NMR spectrometer |
| `"analyzing"` | NMR acquisition is running |
| `"waste_collector"` | Tube is being emptied into waste |
| `"washer1"` | Tube is in the first wash station |
| `"washer2"` | Tube is in the second wash station |
| `"dryer"` | Tube is in the dryer |

### State transition methods

```python
state.tube.filled_tube(id, sample_id)   # Mark tube as filled with sample_id
state.tube.transferring_tube(id)        # Mark tube as being carried by arm
state.tube.in_spectrometer(id)          # Mark tube as inserted into NMR
state.tube.analyzing_tube(id)           # Mark tube as under acquisition
state.tube.in_waste_collector(id)       # Mark tube as in waste station
state.tube.in_washer1(id)              # Mark tube as in washer 1
state.tube.in_washer2(id)              # Mark tube as in washer 2
state.tube.in_dryer(id)               # Mark tube as in dryer
state.tube.empty_tube(id)             # Reset tube to empty, clear sample_id and timestamp
```

### Query methods

```python
state.tube.find_next_filled_tube() -> int   # Tube id with the lowest sample_id in "filled" state; -1 if none
state.tube.find_next_empty_tube() -> int    # First tube id in "empty" state; -1 if none
state.tube.find(type: str) -> int           # First tube id matching a given status string; -1 if none
state.tube.is_all_empty() -> bool           # True if all tubes are empty
state.tube.set_time_finished(id, timestamp) # Record when the NMR acquisition finished
```

### Per-tube data

| Array | Description |
|-------|-------------|
| `tube_status[id]` | Current state string for tube `id` |
| `sample_in_tube[id]` | Sample index currently in tube `id` (−1 if empty) |
| `time_finished[id]` | Timestamp when acquisition finished (−1 if not yet done) |

---

## MessageQueue

A thin thread-safe wrapper around `queue.Queue`. Supports a peek-then-process pattern: read the front message, act on it, then explicitly remove it when done.

```python
from shared_state.message_queue import MessageQueue

mq = MessageQueue()
mq.add_new_message("Hello")      # Enqueue a message
msg = mq.get_front_message()     # Peek at the front (non-destructive)
mq.finish_front_message()        # Remove the front message after processing
mq.no_message()                  # True if queue is empty
```

| Method | Description |
|--------|-------------|
| `add_new_message(msg)` | Append `msg` to the back of the queue |
| `get_front_message() -> str` | Return the front message without removing it |
| `finish_front_message()` | Remove and mark the front message as done |
| `no_message() -> bool` | Return `True` if the queue is empty |

---

## Message Protocol

### Producer channel (`producer_message_queue`) — pipetter ↔ robot arm

| Sender | Message | Meaning |
|--------|---------|---------|
| Robot arm | `"NextSample?"` | Ask pipetter which tube/sample to load next |
| Pipetter | `"TubeId=X"` | Reply with tube slot X to fill next |
| Robot arm | `"PauseRefill"` | Ask pipetter to pause (arm needs the tube) |
| Pipetter | `"PauseRefillOkay"` | Pipetter has paused and is at standby |
| Robot arm | `"ResumeRefill"` | Tell pipetter to resume filling |
| Robot arm | `"ReturnTube"` | Ask pipetter to move away so arm can return tube |
| Pipetter | `"ReadyToReturnTube"` | Pipetter has cleared the path |
| Pipetter | `"Terminate"` | All samples have been processed |

### Consumer channel (`consumer_message_queue`) — robot arm ↔ spectrometer

| Sender | Message | Meaning |
|--------|---------|---------|
| Robot arm | `"NewSampleReady"` | A new tube has been inserted; start acquisition |
| Robot arm | `"DitchSample"` | Abort current acquisition and eject tube |
| Robot arm | `"ShimReference"` | Insert reference sample and run shimming |
| Robot arm | `"RemoveReference"` | Shimming done; remove reference sample |
| Spectrometer | `"Terminate"` | All acquisitions complete |
