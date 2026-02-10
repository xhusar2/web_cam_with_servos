# CameraWebServer (with servo controls)

ESP32-CAM web server example extended with **pan/tilt servo control**. Streams from the camera and lets you move two servos (pan on GPIO 12, tilt on GPIO 13) from the web UI.

**Dependencies:** `ESP32Servo` (install via Arduino Library Manager).

### Pan/tilt controls (web UI)

- **Sliders + step buttons** — Pan (0–180°) and tilt (0–180°) with ±3° step buttons.
- **Invert Pan / Invert Tilt** — Toggles that flip the direction sent to the servos (value becomes `180 − value`). Useful when the servo is mounted opposite to the UI (e.g. “right” moves the camera left). Choices are saved in the browser’s `localStorage` and restored on reload.

### WiFi setup

WiFi credentials are not in the repo. Copy the example and add your own:

```bash
cp wifi_credentials.h.example wifi_credentials.h
```

Edit `wifi_credentials.h` and set `WIFI_SSID` and `WIFI_PASSWORD`. The file `wifi_credentials.h` is gitignored so it won’t be committed.

---

## Editing the web UI (index) with the Python script

The HTML for the web interface is stored inside `camera_index.h` as **gzipped C arrays**. You don’t edit the `.h` by hand. Use `camera_index_tool.py` to **extract** → edit → **embed**.

### 1. Extract HTML from `camera_index.h`

Writes `index_ov2640.html`, `index_ov3660.html`, `index_ov5640.html` in the same folder:

```bash
python camera_index_tool.py extract
```

Or with a custom header path:

```bash
python camera_index_tool.py extract path/to/camera_index.h
```

### 2. Edit the HTML

Edit the file for your camera model (e.g. `index_ov2640.html`). Save when done.

### 3. Embed back into `camera_index.h`

Recompress the HTML and update the C array in the header. **Name** must be one of: `ov2640`, `ov3660`, `ov5640`.

**Print new C block to stdout** (copy/paste manually if you want):

```bash
python camera_index_tool.py embed ov2640 index_ov2640.html
```

**Patch the header in place** (recommended):

```bash
python camera_index_tool.py embed ov2640 index_ov2640.html camera_index.h --inplace
```

With default `camera_index.h` in the script’s directory:

```bash
python camera_index_tool.py embed ov2640 index_ov2640.html --inplace
```

Then rebuild and upload the sketch; the new UI is in the firmware.

### Summary

| Step   | Command |
|--------|--------|
| Extract | `python camera_index_tool.py extract` |
| Edit   | Edit `index_ov2640.html` (or ov3660/ov5640) |
| Embed  | `python camera_index_tool.py embed ov2640 index_ov2640.html --inplace` |

Requires Python 3. Uses only stdlib (`gzip`, `re`, etc.).
