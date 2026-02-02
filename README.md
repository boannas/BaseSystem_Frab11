# Base System 
The Base System with user interfce for FRA263/264 (Robotics Studio III)

## Installation

## Configuration

## How to use
The robot control system operates through a **PC-based UI** communicating with an STM32 controller via Serial (COM) interface.
The system supports multiple operation modes to ensure safe initialization, manual testing, and autonomous execution.

1. Launching the Program 

2. Operation Modes
There are two main control modes available in the system:
    1. Manual / Jog mode
        - Activate this mode by click the `Jog Mode` 
        - The user manually control the `Theta` axes using a joystick.
        - The current values of 

### Protocal : Address & Function
#### Register Address Table
| Address   | Description   | Operation |
|---------- |----------     |---------- |
| 0x00      | Heartbear Protocol | Read/Write |  
| 0x01      | Base System Status | Write      | - 
| 0x02      | Vacuum Status      | Read/Write?| -
| 0x03      | Gripper Movement Status    | Read/Write?| -
| 0x04      | Gripper Movement Actual Status    | Read | -
| 0x05      | Gripper Activate toggle    | Write | 
| 0x10      | Theta Moving Status | Read |
| 0x11      | Theta Actual Position | Read |
| 0x12      | Theta Actual Velocity | Read |
| 0x13      | Theta Actual Acceleration | Read |
| 0x21      | Pick Order         | Write | 
| 0x22      | Place Order        | Write |
| 0x23      | 1st Hole Position | Read |
| 0x25      | 2nd Hole Position | Read |
| 0x26      | 3rd Hole Position | Read |
| 0x27      | 4th Hole Position | Read |
| 0x28      | 5th Hole Position | Read |
| 0x30      | Goal Point (Hole/deg) | Write |

### Data Format
#### 1. Base System Status (0x01) 
Controls the robot’s high-level operating mode and system actions, such as homing, manual operation, or autonomous execution.

| Bit | Data in Binary | Data in Decimal | Description                                     |
| --- | -------------------- | ------- | ----------------------------------------------- |
| 0   | 0000 0000 0000 0001  | 1       | **Home Mode** – Execute homing sequence         |
| 1   | 0000 0000 0000 0010  | 2       | **Manual Mode** – Jog / manual control          |
| 2   | 0000 0000 0000 0100  | 4       | **Autonomous Mode** – Execute automatic program |
| 3   | 0000 0000 0000 1000  | 8       | **Set Holes** – Execute hole-setting routine    |


#### 2. Vacuum Status (0x02) 
Controls the vacuum actuator (ON / OFF).

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0000 = Off | 0 = Off | Vacuum Off |
| 0   | 0000 0000 0000 0001 = Off | 1 = Off | Vacuum On  |


#### 3. Gripper Movement Status (0x03)
Commands the gripper linear movement direction.

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0000 = Backward | 0 = Backward | Backward movement |
| 0   | 0000 0000 0000 0001 = Forward  | 1 = Forward  | Forward movement  |


#### 4. Gripper Movement Actual Status (0x04)
Reports the status of the three limit (lead) switches on the gripper mechanism.

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0001 | 0 / 1 | Lead Switch 1 (0 = Off, 1 = On) |
| 1   | 0000 0000 0000 0010 | 0 / 2 | Lead Switch 2 (0 = Off, 1 = On) |
| 2   | 0000 0000 0000 0100 | 0 / 4 | Lead Switch 3 (0 = Off, 1 = On) |


#### 5. Gripper checkbox (0x05)
Gripper checkbox = enable / disable gripper actuation
- 'ON' -> Robot motion + gripper actions work
- 'OFF' -> Robot motion works, gripper does nothing

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0000 | 0 | gripper `OFF` |
| 0   | 0000 0000 0000 0001 | 1 | gripper `ON`  |


#### 6. Theta Moving Status (0x10) 
Monitor the robot's internal state or which actions is currently performing.


#### 7. Position / Speed / Accelation (0x11 to 0x13)


#### 8. Pick order(0x21), Place order(0x22)
The order of pick and place sent from the Base system to the robot will correspond to the pick and place order displayed in GUI. 

