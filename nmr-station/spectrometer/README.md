# spectrometer

Controls a Magritek Spinsolve 80 MHz benchtop NMR spectrometer over TCP/IP using the Spinsolve XML remote-control protocol. The module sends XML command messages to trigger acquisitions, configure shimming, and set data folders, then parses the response to extract the output data path.

---

## Files

| File | Purpose |
|------|---------|
| `spectrometer.py` | `SpectrometerRemoteControl` — TCP/IP client for the Spinsolve XML protocol |
| `xml_converter.py` | `to_xml_request()` and `load_protocols()` — XML message builder and protocol loader |
| `__init__.py` | Exports `SpectrometerRemoteControl`, `DummySpectrometerRemoteControl`, `load_protocols`, `to_xml_request` |

---

## Connection

The spectrometer runs on the same PC as the Spinsolve software and listens on a local TCP port:

| Setting | Default | `.env` variable |
|---------|---------|----------------|
| Host | `127.0.0.1` | `SPECTROMETER_REMOTE_CONTROL_HOST` |
| Port | `13000` | `SPECTROMETER_REMOTE_CONTROL_PORT` |
| Timeout | 10 s | hardcoded `REMOTE_CONTROL_TIMEOUT` |

A new TCP connection is opened for every request and closed when the response stream ends (timeout-based detection).

---

## SpectrometerRemoteControl

```python
from spectrometer import SpectrometerRemoteControl

sp = SpectrometerRemoteControl()
sp.send_request_to_spinsolve80(xml_message)
print(sp.data_folder)   # path where Spinsolve saved the spectrum
```

### `send_request_to_spinsolve80(request_content, timeout_second=10)`

Sends an XML string to the Spinsolve remote-control port and receives the response until the socket times out. If the response contains a `dataFolder` attribute, it is parsed and stored in `sp.data_folder`.

| Attribute | Description |
|-----------|-------------|
| `sp.data_folder` | Path to the spectrum data folder returned by Spinsolve after acquisition (`None` before first successful acquisition) |

### DummySpectrometerRemoteControl

A drop-in replacement for offline testing. Prints the XML message to stdout instead of sending it over the network.

```python
from spectrometer import DummySpectrometerRemoteControl

sp = DummySpectrometerRemoteControl()
sp.send_request_to_spinsolve80(xml_message)   # prints message, no network call
```

---

## xml_converter

### `to_xml_request(message_type, content) -> str`

Builds a complete XML request string ready to send to the spectrometer.

| `message_type` | `content` type | Description |
|----------------|---------------|-------------|
| `"Start"` | `dict` with `"protocol"` key + option key-value pairs | Start an acquisition protocol |
| `"Set"` | `dict` of field → value | Set one or more instrument fields |
| `"SetFolderName"` | `str` (folder path) | Set the data output folder via `DataFolder/TimeStampTree` |
| `"GetRequest"` | `str` (field name) | Query a single instrument field |

#### Example — start an acquisition

```python
from spectrometer import to_xml_request, SpectrometerRemoteControl

xml = to_xml_request("Start", {
    "protocol": "1D EXTENDED+",
    "Number": 16,
    "AcquisitionTime": 6.4,
    "RepetitionTime": 10,
    "PulseAngle": 30,
})

sp = SpectrometerRemoteControl()
sp.send_request_to_spinsolve80(xml)
```

Generated XML:

```xml
<?xml version="1.0" encoding="utf-8"?>
<Message>
    <Start protocol="1D EXTENDED+">
        <Option name="Number" value="16" />
        <Option name="AcquisitionTime" value="6.4" />
        <Option name="RepetitionTime" value="10" />
        <Option name="PulseAngle" value="30" />
    </Start>
</Message>
```

#### Example — set output folder

```python
xml = to_xml_request("SetFolderName", "C:/NMR_Data/run01")
sp.send_request_to_spinsolve80(xml)
```

#### Example — query a field

```python
xml = to_xml_request("GetRequest", "Solvent")
sp.send_request_to_spinsolve80(xml)
```

---

### `load_protocols() -> dict`

Parses `templates/ProtocolOptions.xml` and returns a dictionary of all protocols supported by the connected Spinsolve unit, including their configurable options and allowed values.

```python
from spectrometer import load_protocols

protocols = load_protocols()
# protocols["1D EXTENDED+"] → {"Number": {"type": "select", "options": [...]}, ...}
```

Used by the Flask web UI (`app.py`) to dynamically populate the protocol selector and parameter forms.

---

## Protocols used in production

| Protocol | Use case | Typical settings |
|----------|----------|-----------------|
| `1D PROTON` | Quick proton spectrum | 16 scans |
| `1D EXTENDED+` | Standard yield measurement | 16 scans, AcquisitionTime 6.4 s, RepetitionTime 10 s, PulseAngle 30° |
| `1D WET SUP` | Solvent-suppressed proton spectrum | — |
| `SHIM` | Periodic re-shimming between samples | `QuickShim1st2nd` (~6 min) |

Shimming is triggered automatically every `MAX_SAMPLE_COUNT_AFTER_SHIMMING` (default: 5) samples. Available shim methods:

| Method | Duration |
|--------|---------|
| `CheckShim` | ~1 min |
| `QuickShim` | ~4 min |
| `QuickShim1st2nd` | ~6 min |
| `PowerShim` | ~40 min |

---

## Approximate acquisition times (1D EXTENDED+)

| Scans | Duration |
|-------|---------|
| 16 | ~2:45 |
| 32 | ~5:15 |
| 63 | ~10:35 |

---

## Integration with Scheduler

`SpectrometerRemoteControl` is wrapped by `NMR_SpectrometerDecision` in `scheduler.py`. The spectrometer thread:

1. Waits for `"NewSampleReady"` on the consumer message queue
2. Sends `SetFolderName` to direct Spinsolve output to the correct data folder
3. Sends the acquisition XML (built via `to_xml_request`) to start the measurement
4. Reads `sp.data_folder` from the response to confirm where the data was saved
5. Sends `"DitchSample"` if acquisition should be aborted, triggering tube ejection by the robot arm
