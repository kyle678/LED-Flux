# LED-Flux

A customizable frontend and backend for driving **WS2812B** (NeoPixel) LED strips. LED-Flux lets you control brightness, power, and playback in real time; trigger built-in presets; and build, save, and replay multi-animation "scenes" from a web UI — all served from a Raspberry Pi on your local network.

---

## Contents

- [Features](#features)
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running](#running)
- [HTTP API reference](#http-api-reference)
- [UDP command protocol](#udp-command-protocol)
- [Animation types & parameters](#animation-types--parameters)
- [Scenes](#scenes)
- [Testing](#testing)
- [Design notes](#design-notes)
- [License](#license)

---

## Features

- **Real-time control** of power, play/pause, and brightness with the physical strip as the source of truth.
- **Quick presets** (e.g. rainbow, solid white) triggered with one click.
- **Scene builder** — layer multiple animations at different start indices, reorder them, hide/show individual layers, and copy/paste animations between scenes.
- **Persistent scenes** saved to a SQLite database and reloadable at any time.
- **Two animation primitives** — `static` (solid color) and `rotating` (a scrolling multi-color gradient) — that compose into arbitrary scenes.
- **Hardware-friendly render loop** that only pushes frames to the strip when something actually changes, keeping the engine responsive even at 1500 pixels.
- **Resilient by design** — malformed commands, out-of-bounds animations, and broken scene entries are logged and skipped rather than crashing the engine.

---

## Architecture

LED-Flux is split into three cooperating processes so that a slow HTTP request can never stall the LED render loop, and the API can be restarted independently of the lights.

```
┌──────────────┐   HTTP/JSON    ┌──────────────┐   UDP/JSON    ┌──────────────┐   SPI/PWM   ┌──────────┐
│              │ ─────────────► │              │ ────────────► │              │ ──────────► │          │
│  React UI    │                │  Flask API   │               │  LED Engine  │             │ WS2812B  │
│ (browser)    │ ◄───────────── │ (api/app.py) │ ◄──────────── │(engine/main) │             │  strip   │
│              │   status JSON  │              │  status reply │              │             │          │
└──────────────┘                └──────┬───────┘               └──────────────┘             └──────────┘
                                       │
                                       ▼
                                ┌──────────────┐
                                │   SQLite     │
                                │ saved scenes │
                                └──────────────┘
```

- **React UI** — the control surface. Talks only to the Flask API over HTTP.
- **Flask API** (`backend/api/`) — a thin HTTP layer. Command routes forward JSON to the engine over UDP (fire-and-forget); the status route does a UDP request/response with a 1-second timeout. It also owns the SQLite database of saved scenes.
- **LED Engine** (`backend/engine/`) — a tight loop that listens for UDP commands (non-blocking, ~10 ms poll), advances active animations, and pushes frames to the physical strip via Adafruit's `neopixel` library. This process must run on the Raspberry Pi.

The API and engine communicate over UDP on `127.0.0.1` by default, so they can run on the same Pi without exposing the engine to the network.

---

## Repository layout

```
LED-Flux/
├── backend/
│   ├── config.ini              # Shared config for API and engine (ports, pixels, DB path)
│   ├── requirements.txt        # Python dependencies (Pi + dev)
│   ├── start_api.sh            # Launch the Flask API
│   ├── start_engine.sh         # Launch the LED engine (needs sudo for GPIO)
│   ├── api/
│   │   ├── app.py              # Flask app factory, DB init, teardown
│   │   ├── db.py               # Shared per-request SQLite connection
│   │   ├── routes.py           # HTTP routes (commands + scene CRUD)
│   │   └── udp_comms.py        # UDP sender/requester to the engine
│   ├── engine/
│   │   ├── main.py             # Socket server + main render loop
│   │   ├── controller.py       # Wraps the NeoPixel strip; compositing & power state
│   │   ├── handlers.py         # Command handlers (brightness, config, power, …)
│   │   ├── utils.py            # Color + gradient math
│   │   └── animations/
│   │       ├── animations.py           # BaseAnimation, StaticAnimation, RotatingAnimation
│   │       └── animation_registry.py   # name → class lookup
│   └── tests/                  # Pytest suite (stubs the Pi hardware)
└── frontend/
    ├── package.json
    └── src/
        ├── App.js              # State, API calls, status syncing
        ├── constants.js        # API base URL + presets
        └── components/         # MainControls, BrightnessSlider, QuickPresets,
                                #   SavedScenes, ConfigBuilder
```

---

## Requirements

**Hardware**

- Raspberry Pi (any model with GPIO)
- WS2812B / NeoPixel LED strip
- Strip data line wired to **GPIO 18** or **GPIO 21** (the only two pins the engine accepts)
- An appropriately sized 5V power supply for your strip

**Software**

- Python 3.9+ on the Pi
- Node.js 16+ and npm (to build/serve the frontend)

> **Note:** The engine imports `neopixel` and `board`, which only work on the Pi. You can develop and test everything else on another machine — see [Testing](#testing).

---

## Installation

### Backend (on the Raspberry Pi)

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Configuration

All backend configuration lives in `backend/config.ini`:

```ini
[engine]
udp_ip = 127.0.0.1      ; address the engine binds to / the API sends to
udp_port = 5005

[flask]
host = 0.0.0.0          ; 0.0.0.0 exposes the API to the LAN
port = 5000

[pixels]
pin_number = 18         ; GPIO pin (18 or 21)
num_pixels = 1500       ; number of LEDs on the strip
brightness = .2         ; 0.0–1.0

[database]
path = api/led_configs.db

[logging]
level = INFO
file = logs/controller.log
```

Both the API and the engine read the same file, so they can't disagree about ports or pixel count.

### Frontend API endpoint

The frontend defaults to `http://192.168.1.101:5000/api`. Point it at your Pi without editing source by creating `frontend/.env`:

```
REACT_APP_API_BASE=http://<your-pi-ip>:5000/api
```

The strip length (`num_pixels`) used by presets is read live from the engine's status response, so you only need to set it in `config.ini`.

---

## Running

The engine needs **two** processes running on the Pi. Start each in its own terminal (from `backend/`):

```bash
# 1. LED engine — needs root for GPIO/PWM access
./start_engine.sh          # sudo venv/bin/python -m engine.main

# 2. Flask API
./start_api.sh             # python api/app.py
```

Then start the frontend (from `frontend/`):

```bash
npm start                  # dev server, http://localhost:3000
# or build static assets for production:
npm run build
```

Open the UI in a browser and it will connect to the API at the address configured above.

---

## HTTP API reference

Base path: `/api`

### Control routes

These forward a command to the engine. They respond immediately after sending (the engine does not ack), except `status`, which waits for a reply.

| Method | Path              | Body (`action` + `data`)                                   | Purpose                            |
| ------ | ----------------- | ---------------------------------------------------------- | ---------------------------------- |
| GET    | `/api/status`     | —                                                          | Read current engine state          |
| POST   | `/api/brightness` | `{ "action": "brightness", "data": { "value": 0.0-1.0 }}` | Set global brightness              |
| POST   | `/api/power`      | `{ "action": "power", "data": { "value": "on"/"off" }}`   | Power the strip on/off             |
| POST   | `/api/pause`      | `{ "action": "pause", "data": { "value": "on"/"off" }}`   | Play/pause animation updates       |
| POST   | `/api/animation`  | `{ "action": "animation", "data": { … } }`                | Play a single animation            |
| POST   | `/api/config`     | `{ "action": "config", "data": { name, animations } }`    | Play a full scene                  |
| POST   | `/api/clear`      | `{ "action": "clear", "data": {} }`                        | Clear the strip and all animations |

`GET /api/status` returns:

```json
{
  "status": "success",
  "data": {
    "active": true,
    "power": true,
    "brightness": 0.2,
    "num_pixels": 1500,
    "animations": ["StaticAnimation", "RotatingAnimation"]
  }
}
```

If the engine is offline, status returns `503` with `{ "status": "error", "message": "Engine timeout" }`.

### Scene database routes

| Method | Path                    | Purpose                                    |
| ------ | ----------------------- | ------------------------------------------ |
| GET    | `/api/configs`          | List all saved scenes                      |
| POST   | `/api/configs`          | Create or update a scene (upsert by name)  |
| GET    | `/api/configs/<name>`   | Fetch one scene by name                    |
| DELETE | `/api/configs/<name>`   | Delete a scene                             |

A scene is `{ "name": "Party Mode", "animations": [ … ] }`. Scenes are stored in SQLite with a unique name constraint; saving an existing name overwrites it.

---

## UDP command protocol

The API and engine speak JSON over UDP. Each datagram is a command object:

```json
{ "action": "<name>", "data": { … } }
```

Supported actions (see `backend/engine/handlers.py`):

| Action       | `data` payload                              | Effect                                                        |
| ------------ | ------------------------------------------- | ------------------------------------------------------------- |
| `brightness` | `{ "value": 0.0-1.0 }`                      | Set strip brightness (invalid values ignored)                 |
| `power`      | `{ "value": "on"/"off" }`                   | Power on (re-renders) / off (blanks the strip)                |
| `pause`      | `{ "value": "on"/"off" }`                   | `on` resumes **and powers on**; `off` freezes the last frame  |
| `animation`  | single animation object                     | Clear, power on, and play one animation                       |
| `config`     | `{ name, animations: [ … ] }`               | Clear, power on, and load a full scene                        |
| `clear`      | `{}`                                        | Drop all animations and blank the strip                       |
| `get_status` | —                                           | Reply with the status object shown above                      |

Malformed packets, non-object payloads, and unknown actions are logged and dropped.

---

## Animation types & parameters

Animations are selected by `animation_type` and constructed from the following parameters (defaults in parentheses). Unknown types are skipped.

| Parameter        | Default            | Description                                                       |
| ---------------- | ------------------ | ---------------------------------------------------------------- |
| `animation_type` | —                  | `"static"` or `"rotating"`                                        |
| `name`           | `"new animation"`  | Human-readable label                                             |
| `num_pixels`     | `10`               | Length of this animation's segment                              |
| `start_index`    | `0`                | Where the segment begins on the strip (overruns are cropped)     |
| `brightness`     | `1`                | Per-animation dim factor, `0.0-1.0`                             |
| `loop_duration`  | `5`                | Seconds for one full cycle (rotating)                           |
| `target_fps`     | `30`               | Max update rate                                                  |
| `colors`         | 3-color default    | List of `[r, g, b]` triples                                     |
| `hide`           | `false`            | Render the segment as black (a "gap") without deleting it        |
| `wrap`           | `true`             | Rotating: loop the gradient back to the first color seamlessly   |

**`static`** — fills its segment with a single solid color (`colors[0]`). Renders once and stops pushing frames until something changes.

**`rotating`** — builds a multi-color gradient across the segment and scrolls it over `loop_duration`. Skips redundant pushes when the rotation index hasn't advanced.

Example single animation:

```json
{
  "animation_type": "rotating",
  "name": "rainbow",
  "num_pixels": 1500,
  "start_index": 0,
  "loop_duration": 10,
  "target_fps": 30,
  "colors": [[255,0,0],[255,255,0],[0,255,0],[0,255,255],[0,0,255],[255,0,255]]
}
```

---

## Scenes

A scene is an ordered list of animations that render together, each on its own segment of the strip (defined by `start_index` + `num_pixels`). The scene builder in the UI lets you:

- Add, edit, reorder, and delete animation layers
- Warn on overlapping segments before adding
- Hide/show individual layers (renders that segment black)
- Copy an animation and paste it into another scene (via `localStorage`)
- Test the current scene live, save it to the database, or revert unsaved changes

Because each animation carries its own `start_index`, you can, for example, run a rotating rainbow across pixels 0–999 and a static warm-white section across 1000–1499 in the same scene.

---

## Testing

The backend ships with a pytest suite in `backend/tests/` that stubs the Pi-only `neopixel` and `board` modules, so it runs on any machine.

```bash
cd backend
python -m pytest tests
```

The suite covers the gradient/rotation math, the controller's compositing and cropping, power/pause semantics, render-once efficiency, and every command handler.

The frontend uses Create React App's test runner:

```bash
cd frontend
npm test
```

---

## Design notes

- **Process separation over UDP** keeps the render loop isolated from HTTP latency and lets the API restart without disturbing the lights.
- **Frames are only pushed when they change.** `show()` costs meaningful wire time per pixel at 1500 LEDs, so statics render once and rotating animations skip frames whose rotation index hasn't advanced.
- **Playing implies power-on.** Both the config and pause handlers power the strip on when starting playback, and the UI re-reads engine status after each command rather than assuming its own state — the strip is always the source of truth.
- **The engine degrades gracefully.** Out-of-bounds animations are cropped instead of raising, a single bad animation in a scene is skipped rather than aborting the whole scene, and an animation that throws every frame is dropped so the engine stays responsive.

---

## License

Released under the [MIT License](LICENSE). © 2025 Kyle678
