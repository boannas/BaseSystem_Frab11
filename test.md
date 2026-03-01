# Base System
PC-based Base System with user interface for **FRA263/264 (Robotics Studio III)**.  
The UI communicates with an STM32 controller over **Modbus RTU via Serial (COM)**.

---

## Configuration

### Serial Port (Windows – STM32 via ST-Link)

1. Open **Device Manager**
2. Expand **Ports (COM & LPT)**
3. Find:

   `STMicroelectronics STLink Virtual COM Port (COMx)`

4. Enter that COM number (x) in the UI.

Example:  
If you see `... (COM3)` -> enter `3` in the Connect field.

---

## How to Use

The Base System operates through a **PC UI** communicating with the robot controller via Serial (COM).  
The system supports multiple modes for safe initialization, manual operation, automatic execution, and testing.

1. **Launching the program**
   - Run the backend and open the UI.
   - Ensure backend is running before pressing **Connect**.

2. **Operation Modes**
   - Manual (Jog)
   - Go Home
   - Auto
   - Test

---

# Operating Modes

The Base System provides four operating modes to control the robot.  
Each mode is designed for a specific level of operation: manual control, automatic task execution, or system testing.

---

## 1) Manual Mode

Manual Mode allows the operator to directly control robot motion and gripper actions.

### 1.1 Gripper Control

Available commands:

- **UP** -> Move gripper cylinder upward
- **DOWN** -> Move gripper cylinder downward
- **OPEN** -> Release object
- **CLOSE** -> Grip object
- **PICK** -> Execute pick sequence
- **PLACE** -> Execute place sequence

### 1.2 Jog Control

Jog mode allows **discrete step movement**.

Operator inputs:
- Step size (degree)
- Direction:
  - **CCW (Counter-Clockwise)** -> Positive value
  - **CW (Clockwise)** -> Negative value

<!-- Jog writes a signed `int16` value to register `0x14`. -->

Examples:
- `+10` -> Move +10 degrees (CCW)
- `-10` -> Move -10 degrees (CW)

---

## 2) Go Home

The **Go Home** command moves the robot to its predefined home position.

---

## 3) AUTO Mode

AUTO Mode executes higher-level motion sequences.

### 3.1 Pick and Place

Executes a sequence of pick and place operations.

Operator sets:
- Number of targets
- Pick hole sequence
- Place hole sequence
- Direction for each move (CCW / CW)

<!-- Hole commands use registers `0x21–0x30` and are encoded as: -->

<!-- - `abs(value)` = hole index (1–5)
- `value > 0` -> CCW direction
- `value < 0` -> CW direction -->

### 3.2 Point-to-Point (P2P)

Moves the robot directly to a target relative to Home.

Two selectable units:
- **Degree**
- **Index**

<!-- Registers used:
- `0x31` -> Unit selection (0 = Degree, 1 = Index)
- `0x32` -> Target value (signed int16) -->

---

## 4) TEST Mode

TEST Mode is used for validation and characterization.

### 4.1 Performance Mode
Used to test dynamic capability.

Operator sets:
- Speed
- Acceleration

<!-- Registers:
- `0x16` -> Speed
- `0x17` -> Acceleration -->

### 4.2 Precision Mode
Used to test repeatability.

Operator sets:
- Initial position
- Target position
- Repeat count

<!-- Registers:
- `0x18` -> Initial position
- `0x19` -> Target position
- `0x20` -> Repeat count (+ = degree, − = index) -->

---

## Mode Summary

| Mode   | Level      | Purpose |
|--------|------------|---------|
| Manual | Low-level  | Direct actuator control |
| Go Home | Reset     | Move to reference position |
| AUTO   | Task-level | Execute pick/place or P2P |
| TEST   | Validation | Evaluate speed and precision |

---

# Protocol: Address & Function

## Register Address Table

| Address   | Description | Operation |
|----------:|------------|----------|
| 0x00      | Heartbeat Protocol | Read/Write |
| 0x01      | Base System Mode | Write |
| 0x02      | Gripper Status | Write |
| 0x03      | Gripper Movement Status | Write |
| 0x04      | Gripper Movement Actual Status | Read |
| 0x05      | Gripper Enable Checkbox | Write |
| 0x10      | Theta Moving Status | Read |
| 0x11      | Theta Actual Position | Read |
| 0x12      | Theta Actual Velocity | Read |
| 0x13      | Theta Actual Acceleration | Read |
| 0x14      | Jog Command | Write |
| 0x15      | Test Mode (Performance/Precision) | Write |
| 0x16      | (Test) Performance Speed | Write |
| 0x17      | (Test) Performance Acceleration | Write |
| 0x18      | (Test) Precision Initial Position | Write |
| 0x19      | (Test) Precision Target Position | Write |
| 0x20      | (Test) Precision Repeat (sign = unit) | Write |
| 0x21–0x25 | Pick Hole #1–#5 (sign = direction) | Write |
| 0x26–0x30 | Place Hole #1–#5 (sign = direction) | Write |
| 0x31      | Point-to-Point Unit | Write |
| 0x32      | Point-to-Point Value | Write |
| 0x33      | Emergency Status | Read |
| 0x34      | Stop Process | Write |

---

# Modbus Protocol Specification
## Mixed Register Types (uint16 Default + int16)

This section defines data types and encoding rules.

---

## 1) General Rules

All Modbus holding registers are **16-bit**.

- Default interpretation: **uint16 (0–65535)**
- Some registers are explicitly defined as **int16 (signed, two’s complement)**

---

## 2) Data Type Rules

### 2.1 Default Type: uint16

Unless otherwise specified, registers are interpreted as:
`uint16 (0–65535)`

Used for:
- Bitfields
- Enums
- Status flags
- Mode selection
- Control flags

---

### 2.2 Signed Type: int16 (Two’s Complement)

The following registers are **signed int16**:
```
0x11, 0x12, 0x13,
0x14,
0x16, 0x17,
0x18, 0x19,
0x20,
0x21–0x30,
0x32
```


Range: `-32768 to +32767`

#### Write Rule (PC -> Robot)
```
If value < 0:
    raw = 65536 + value
Else:
    raw = value
```


#### Read Rule (Robot -> PC)
```
If raw ≥ 32768:
    value = raw - 65536
Else:
    value = raw
```


---

### 2.3 Scaled Real Values (×10 Format)

Registers:
- `0x11` – Theta Position
- `0x12` – Theta Speed
- `0x13` – Theta Acceleration

Encoding rule:
- Robot sends: `raw = round(actual_value * 10)`
- PC decodes: `actual_value = int16(raw) / 10.0`

Examples:
- `123.4` -> `1234`
- `-12.3` -> int16 `-123` -> raw `65413 (0xFF85)`

---

## 3) Register Map

| Addr | Name | Direction | Access | Type | Description |
|------|------|----------|--------|------|------------|
| 0x00 | Heartbeat | R/W | R/W | uint16 | YA=22881, HI=18537 |
| 0x01 | Base System Status | BS->R | W | uint16 (bitfield) | Operating mode flags |
| 0x02 | Gripper Command | BS->R | W | uint16 (enum) | Open/Close/Pick/Place |
| 0x03 | Gripper Z Movement | BS->R | W | uint16 (enum) | Up/Down |
| 0x04 | Gripper Reed Status | R->BS | R | uint16 (bitfield) | Reed switch states |
| 0x05 | Gripper Enable | BS->R | W | uint16 (enum) | 0=Disable, 1=Enable |
| 0x10 | Theta Moving Status | R->BS | R | uint16 (bitfield) | Motion state flags |
| 0x11 | Theta Position | R->BS | R | int16 (scaled ×10) | Position |
| 0x12 | Theta Speed | R->BS | R | int16 (scaled ×10) | Speed |
| 0x13 | Theta Acceleration | R->BS | R | int16 (scaled ×10) | Acceleration |
| 0x14 | Jog Command | BS->R | W | int16 | Signed degrees |
| 0x15 | Test Mode | BS->R | W | uint16 (enum) | 0=Precision, 1=Performance |
| 0x16 | Test Speed | BS->R | W | int16 | Performance speed |
| 0x17 | Test Acceleration | BS->R | W | int16 | Performance acceleration |
| 0x18 | Test Initial Position | BS->R | W | int16 | Precision initial |
| 0x19 | Test Target Position | BS->R | W | int16 | Precision target |
| 0x20 | Test Repeat + Unit | BS->R | W | int16 | abs(value)=repeat, sign=unit |
| 0x21–0x25 | Pick Hole #1–#5 | BS->R | W | int16 | abs(value)=hole index, sign=direction |
| 0x26–0x30 | Place Hole #1–#5 | BS->R | W | int16 | abs(value)=hole index, sign=direction |
| 0x31 | P2P Unit | BS->R | W | uint16 | 0=Degree, 1=Index |
| 0x32 | P2P Value | BS->R | W | int16 | Signed target |
| 0x33 | Emergency Status | R->BS | R | uint16 | 0=Normal, 1=Pressed |
| 0x34 | Stop Process | BS->R | W | uint16 | 0=Normal, 1=Stop |

---

## 4) Detailed Definitions

### 4.1 Base System Status (0x01) — bitfield (uint16)

| Bit | Value | Meaning |
|-----|-------|---------|
| 0 | 1  | Home |
| 1 | 2  | Manual (Jog) |
| 2 | 4  | Auto |
| 3 | 8  | Set Home |
| 4 | 16 | Test Mode |

### 4.2 Gripper Command (0x02) — enum (uint16)

| Value | Meaning |
|------:|---------|
| 0 | Open |
| 1 | Close |
| 2 | Pick |
| 3 | Place |

### 4.3 Gripper Movement (0x03) — enum (uint16)

| Value | Meaning |
|------:|---------|
| 0 | Up |
| 1 | Down |

### 4.4 Reed Switch Status (0x04) — bitfield (uint16)

| Bit | Meaning |
|-----|--------|
| 0 | Reed 1 |
| 1 | Reed 2 |
| 2 | Reed 3 |

### 4.5 Theta Moving Status (0x10) — bitfield (uint16)

| Bit | Meaning |
|-----|--------|
| 0 | Homing |
| 1 | Go Pick |
| 2 | Go Place |
| 3 | Go Point |
| none | Idle |

### 4.6 Jog Command (0x14) — int16
- Positive -> CCW
- Negative -> CW

### 4.7 Test Repeat + Unit (0x20) — int16
- abs(value) = repeat count
- value > 0 -> degree
- value < 0 -> index

### 4.8 Pick / Place Hole Command (0x21–0x30) — int16
- abs(value) = hole index (1–5)
- value > 0 -> CCW
- value < 0 -> CW

Examples:
- `+3` -> hole 3 CCW
- `-3` -> hole 3 CW

### 4.9 Emergency Status (0x33) — uint16

| Value | Meaning |
|------:|---------|
| 0 | Not pressed |
| 1 | Pressed |

### 4.10 Stop Process (0x34) — uint16

| Value | Meaning |
|------:|---------|
| 0 | Normal |
| 1 | Stop |

---

## 5) Heartbeat Protocol (0x00)

Robot writes: `YA = 22881`  
PC replies: `HI = 18537`

If YA is not received within timeout -> connection is considered lost.