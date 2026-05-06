# Testing the Base System (students)

This guide helps you **verify the WebSocket server** and optionally **exercise Modbus** with the real COM port. It complements the register reference in [`README.md`](README.md).

---

## 1. Prerequisites

- Python 3.10+ with a virtual environment (see [`README.md`](README.md)).
- Dependencies installed: `pip install -r requirements.txt`
- For hardware tests: STM32 connected, correct **COM** number in Device Manager, firmware using **19200 8E1** and the same register map as [`protocol.py`](protocol.py).

---

## 2. Start the backend

From the project root (with venv activated):

```bash
python server_111.py
```

Expected console output:

```text
WebSocket Server running ws://localhost:8765
```

The server listens on **`ws://localhost:8765`**. Only **one** stats loop runs per connection; reconnecting cancels the previous client’s stats task.

---

## 3. What you should see without sending commands

When a client connects, the server immediately sends one **STATS** JSON object (initial connection message). After that, **`stats_loop`** pushes **STATS** repeatedly while the connection stays open.

### 3.1 Initial message (shape)

Fields may vary slightly; common keys include:

| Key | Meaning |
|-----|--------|
| `type` | `"STATS"` |
| `message` | Present on first message only (e.g. connected notice). |
| `pos`, `speed`, `accel` | From Modbus reads **0x28–0x30** when `routine()` succeeds; otherwise may stay `"--"`. |
| `gripper` | String derived from reeds (**READ 0x26**), e.g. `"Up / Open"`. |
| `mode` | From **READ 0x27** (e.g. `Idle`, `Homing`). |
| `emergency` | From **READ 0x31**. |
| `connected` | Serial connected (initial); ongoing stream uses `heartbeat` for liveness. |

### 3.2 Streaming STATS

Repeated messages look like:

```json
{
  "type": "STATS",
  "pos": 0.0,
  "speed": 0.0,
  "accel": 0.0,
  "gripper": "Idle / Open",
  "mode": "Idle",
  "emergency": false,
  "heartbeat": true
}
```

- If the serial link is down or the robot never sends the expected heartbeat (**YA** on **0x00**), `heartbeat` can become **false** even if the port opened successfully.

---

## 4. WebSocket command format

Send **one JSON object per message**. The server uses:

- `mode` — high-level category (e.g. `"Connect"`, `"Manual"`, `"Auto"`).
- `action` — specific command within that category.
- Other keys as needed (numbers, strings, arrays).

On success, many handlers **do not** send an acknowledgment JSON (they `continue`). If `mode` / `action` is not recognized, you get:

```json
{
  "mode": "Error",
  "message": "Unsupported command: mode=..., action=..."
}
```

---

## 5. Example messages (copy-paste for labs)

Replace `3` with your COM number. Default **slave** is **21** if omitted.

### 5.1 Connect to serial

```json
{
  "mode": "Connect",
  "action": "connect_port",
  "port": 3,
  "slave": 21
}
```

**Response:**

```json
{
  "mode": "Connect",
  "action": "connect_port",
  "status": "success",
  "message": "Connected to COM3 (slave 21)"
}
```

### 5.2 Operating mode (WRITE 0x01)

Jog / manual mode:

```json
{
  "mode": "Manual",
  "action": "set_manual"
}
```

Go home:

```json
{
  "mode": "Home",
  "action": "go_home"
}
```

Auto mode:

```json
{
  "mode": "Auto",
  "action": "set_auto"
}
```

Test mode:

```json
{
  "mode": "Test",
  "action": "set_test"
}
```

### 5.3 Gripper (WRITE 0x02 / 0x03)

```json
{ "mode": "Manual", "action": "gripper_up" }
```

```json
{ "mode": "Manual", "action": "gripper_open" }
```

```json
{ "mode": "Manual", "action": "gripper_pick" }
```

### 5.4 Jog (WRITE 0x05)

`direction`: `"CCW"` → positive signed value, anything else (e.g. `"CW"`) → negative.

```json
{
  "mode": "Manual",
  "action": "jog",
  "value": 10,
  "direction": "CCW"
}
```

### 5.5 Soft stop (WRITE 0x25)

```json
{
  "mode": "Stop",
  "action": "stop"
}
```

### 5.6 Point-to-point (WRITE 0x23, 0x24)

`unit` must match Python strings: `"degree"` or `"index"`.

```json
{
  "mode": "Auto",
  "action": "point_to_point",
  "unit": "degree",
  "value": 45
}
```

### 5.7 Performance test (WRITE 0x06, 0x07, 0x08)

```json
{
  "mode": "Test",
  "action": "performance",
  "speed": 100,
  "accel": 50
}
```

### 5.8 Precision test (WRITE 0x06, 0x09, 0x10, 0x11)

`unit`: `"degree"` → positive sign on repeat encoding; `"index"` → negative (see `server_111.py`).

```json
{
  "mode": "Test",
  "action": "precision",
  "init_pos": 0,
  "tar_pos": 90,
  "repeat": 5,
  "unit": "degree"
}
```

### 5.9 Pick and place (WRITE 0x12–0x22, 0x04)

`sequence` and `directions` must align: encoding uses the first element of `sequence` and pairs the rest with `directions`. Adjust to match your UI and lab procedure.

```json
{
  "mode": "Auto",
  "action": "pick_place",
  "sequence": [1, 2, 3, 4],
  "directions": ["CCW", "CW", "CCW"],
  "use_gripper": true
}
```

---

## 6. Minimal Python WebSocket client (optional)

Save as `ws_smoke_test.py` in the project folder (or run from REPL). Requires `websockets` installed.

```python
import asyncio
import json
import websockets

URI = "ws://localhost:8765"

async def main():
    async with websockets.connect(URI) as ws:
        # Drain first STATS / messages briefly
        raw = await asyncio.wait_for(ws.recv(), timeout=2.0)
        print("recv:", raw[:200], "...")

        await ws.send(json.dumps({
            "mode": "Connect",
            "action": "connect_port",
            "port": 3,
            "slave": 21,
        }))
        ack = await ws.recv()
        print("connect:", ack)

asyncio.run(main())
```

Change `port` to your COM number. This only checks **connectivity** and **Connect** handling; robot motion requires safe lab conditions and instructor approval.

---

## 7. Checklist (lab report ideas)

| Step | Pass criteria |
|------|----------------|
| Server starts | Console shows `ws://localhost:8765`. |
| Client connects | First STATS JSON received. |
| Connect command | Response `status`: `success` with correct COM. |
| After connect | STATS `pos`/`speed`/`accel` update from `"--"` when `routine()` reads succeed. |
| Heartbeat | `heartbeat` true when firmware sends YA and PC answers HI (see [`README.md`](README.md)). |
| Manual / jog | Observe expected register writes in console if debug logging is enabled in `protocol.py`. |
| Emergency | Trigger E-stop safely per lab rules; `emergency` reflects **READ 0x31**. |

---

## 8. Troubleshooting

| Symptom | Things to check |
|--------|-------------------|
| `Failed to connect to COMx` | Wrong COM number, cable, driver, or port in use by another program. |
| STATS stay `"--"` | Slave ID mismatch, wrong baud/parity, or firmware not responding to Modbus read. |
| `heartbeat` false | Heartbeat not implemented on firmware, timeout too strict, or no YA on **0x00**. |
| `Unsupported command` | Typo in `mode` or `action`; compare exactly to `server_111.py`. |
| Invalid JSON | Send a single JSON object per message; use double quotes. |

---

## 9. Safety

Always follow your **course and lab safety rules**. Use **soft stop** and **emergency** procedures as instructed. Do not send motion commands until the workspace is clear and the teaching team approves.
