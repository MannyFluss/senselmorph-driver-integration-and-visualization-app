# Sensel Morph — Linux Driver Integration & Live Visualizer

## Demo

[![Sensel Morph Linux Visualizer Demo](https://img.youtube.com/vi/LYtQcPp1yzM/maxresdefault.jpg)](https://www.youtube.com/watch?v=LYtQcPp1yzM)

A complete Linux setup for the [Sensel Morph](https://sensel.com/pages/the-sensel-morph) pressure pad — from raw USB access to a GPU-accelerated live heatmap visualizer running in your browser.

The Sensel Morph has 19,425 independent pressure sensors (185×105 grid). This project gives you full access to all of them.



---

## What's included

| File | Purpose |
|---|---|
| `99-sensel.rules` | udev rule — gives your user permission to read the device without sudo |
| `server.py` | Python WebSocket server — reads the Sensel and streams data at 60fps |
| `visualizer.html` | GPU-accelerated WebGL heatmap — open in any browser |
| `start.sh` | One-command launcher |
| `read_sensor.py` | Terminal sensor reader — prints raw contact/force data |
| `test_device.py` | Quick device detection test |

---

## Requirements

- Linux (tested on Fedora 43)
- Python 3.8+
- A Sensel Morph connected via USB

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/MannyFluss/senselmorph-driver-integration-and-visualization-app
cd senselmorph-driver-integration-and-visualization-app
```

### 2. Install system dependencies

```bash
sudo dnf install gcc-c++ python3-devel SDL2-devel freetype-devel  # Fedora
# or
sudo apt install build-essential python3-dev libsdl2-dev libfreetype-dev  # Ubuntu/Debian
```

### 3. Install the Sensel C library

The pre-built `.deb` in `sensel-api/sensel-install/` contains the shared library. Extract and install it:

```bash
mkdir -p /tmp/sensel-extract
cd /tmp/sensel-extract
ar x ~/path/to/repo/sensel-api/sensel-install/senselliblinux0.8.2.deb
tar xf data.tar.xz
sudo cp usr/lib/libsensel.so /usr/lib/libsensel.so
sudo cp usr/lib/libsenseldecompress.so /usr/lib/libsenseldecompress.so
sudo ldconfig
```

### 4. Install Python dependencies

```bash
pip install websockets numpy
```

### 5. Set up device permissions

Copy the udev rule so you can read the device without running as root:

```bash
sudo cp 99-sensel.rules /etc/udev/rules.d/
sudo usermod -aG input,dialout $USER
sudo udevadm control --reload-rules && sudo udevadm trigger
```

Log out and back in for the group changes to take effect.

### 6. Disable ModemManager (optional but recommended)

ModemManager probes serial ports on plug-in and can interfere with the Sensel. The `start.sh` script handles this automatically, but you can permanently ignore the device:

```bash
sudo cp 99-sensel.rules /etc/udev/rules.d/
```

Or disable ModemManager entirely if you don't use mobile broadband:

```bash
sudo systemctl disable --now ModemManager
```

---

## Running

```bash
./start.sh
```

This will:
1. Stop ModemManager temporarily
2. Start the WebSocket server (auto-retries until device is found)
3. Open `visualizer.html` in your browser

Press `Ctrl+C` to stop. ModemManager is restarted on exit.

---

## Visualizer controls

| Key / Button | Action |
|---|---|
| `R` | Rotate between landscape and portrait |
| `A` | Toggle auto-scale (adapts to your pressure range) |
| Record button | Capture a GIF of the canvas |

### Tunable parameters (right panel)

- **Max force** — reference for 100% pressure (auto or manual)
- **Blur sigma / Coarse sigma** — how far pressure diffuses from each sensor cell
- **Fine/coarse mix** — blend between sharp sensor detail and soft glow
- **Gamma** — tone curve (lower = more sensitive to light touches)
- **Lerp speed** — how fast the visualization responds to changes
- **Contact fade in/out** — smoothness of touch appear/disappear transitions

---

## How it works

### Why not a kernel driver?

The Sensel Morph is a class-compliant USB HID composite device — Linux recognizes it out of the box. No kernel module needed. The Sensel C library (`libsensel`) communicates with the device over its serial interface (`/dev/ttyACM0`).

### Architecture

```
Sensel Morph (USB)
       │
   /dev/ttyACM0   ← dialout group permission
       │
   libsensel.so   ← official Sensel C library (MIT licensed)
       │
   sensel.py      ← Python wrapper (ctypes)
       │
   server.py      ← asyncio WebSocket server, 60fps broadcast
       │
   ws://localhost:8765
       │
   visualizer.html ← WebGL fragment shader, GPU heatmap
```

### The pressure data

Each frame contains:
- **Force array** — 185×105 float32 values (one per sensor cell), transmitted as base64
- **Contacts** — up to 16 algorithmically detected touch regions with position (mm), force (g), area (mm²), and state

The visualizer uses the full force array for rendering — not just the 16 contact points — so every sensor contributes to the image.

---

## Acknowledgements

- [Sensel API](https://github.com/sensel/sensel-api) — official open-source C library (MIT license)
- The Sensel Morph was discontinued in 2022 but remains one of the highest-resolution pressure sensing surfaces ever made available to consumers

---

## License

MIT
