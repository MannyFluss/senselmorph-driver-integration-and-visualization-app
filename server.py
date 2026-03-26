import sys
import asyncio
import json
import base64
import struct
import threading
import numpy as np

sys.path.insert(0, './sensel-api/sensel-lib-wrappers/sensel-lib-python')
import sensel
import websockets

# ─── Sensor reader (blocking, runs in background thread) ──────────────────────

class SenselReader(threading.Thread):
    ROWS = 105
    COLS = 185

    def __init__(self):
        super().__init__(daemon=True)
        self.lock = threading.Lock()
        self.force = np.zeros(self.ROWS * self.COLS, dtype=np.float32)
        self.contacts = []
        self.running = False
        self._handle = None
        self._frame = None

    def open(self):
        err, dl = sensel.getDeviceList()
        if dl.num_devices == 0:
            raise RuntimeError("No Sensel device found — is ModemManager stopped?")
        err, self._handle = sensel.openDeviceByID(dl.devices[0].idx)
        err, self._frame = sensel.allocateFrameData(self._handle)
        sensel.setFrameContent(
            self._handle,
            sensel.FRAME_CONTENT_PRESSURE_MASK | sensel.FRAME_CONTENT_CONTACTS_MASK
        )
        sensel.startScanning(self._handle)
        print(f"Sensel opened — {self.ROWS}×{self.COLS} sensor grid")

    def close(self):
        self.running = False
        if self._handle:
            sensel.stopScanning(self._handle)
            sensel.freeFrameData(self._handle, self._frame)
            sensel.close(self._handle)

    def run(self):
        self.running = True
        n = self.ROWS * self.COLS
        while self.running:
            sensel.readSensor(self._handle)
            err, num_frames = sensel.getNumAvailableFrames(self._handle)
            for _ in range(num_frames):
                sensel.getFrame(self._handle, self._frame)
                f = self._frame
                arr = np.array([f.force_array[i] for i in range(n)], dtype=np.float32)
                contacts = []
                for i in range(f.n_contacts):
                    c = f.contacts[i]
                    contacts.append({
                        'id': int(c.id),
                        'x': round(float(c.x_pos), 2),
                        'y': round(float(c.y_pos), 2),
                        'force': round(float(c.total_force), 1),
                        'area': round(float(c.area), 2),
                        'state': int(c.state),
                    })
                with self.lock:
                    self.force = arr
                    self.contacts = contacts

    def snapshot(self):
        with self.lock:
            # Encode force as base64 binary (float32) — compact and fast
            force_b64 = base64.b64encode(self.force.tobytes()).decode('ascii')
            return {
                'force': force_b64,
                'rows': self.ROWS,
                'cols': self.COLS,
                'contacts': list(self.contacts),
            }


# ─── WebSocket server ──────────────────────────────────────────────────────────

reader = SenselReader()
clients = set()

async def handler(ws):
    clients.add(ws)
    print(f"Client connected ({len(clients)} total)")
    try:
        await ws.wait_closed()
    finally:
        clients.discard(ws)
        print(f"Client disconnected ({len(clients)} total)")

async def broadcast_loop():
    while True:
        if clients:
            data = json.dumps(reader.snapshot())
            await asyncio.gather(
                *[ws.send(data) for ws in list(clients)],
                return_exceptions=True
            )
        await asyncio.sleep(1 / 60)  # 60fps target

async def main():
    # Retry until device is available — handles ModemManager race and unplug/replug
    while True:
        try:
            reader.open()
            break
        except RuntimeError as e:
            print(f"Waiting for device: {e} — retrying in 2s...")
            await asyncio.sleep(2)

    reader.start()

    print("WebSocket server starting on ws://localhost:8765")
    print("Open visualizer.html in your browser")

    async with websockets.serve(handler, 'localhost', 8765):
        await broadcast_loop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        reader.close()
        print("\nServer stopped.")
