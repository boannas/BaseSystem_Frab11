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
        - Activate this mode by click the `Jog Mode` xxxxxxxx
        - The user manually control the `Theta` using a joystick.
        - The current values of `Theta` is displayed live in GUI
        - The user can move `Theta` in incremental degree by input the value and select direction (clockwise or counter clockwise)
        - The user able to control the gripper state by toggle button for both `Upward` / `Downward` and `Grip` / `Release`

    2. Auto mode
        - Point to Point: the user can move the `Theta` by giving value (can select for Degree or saved hole index). [can repeatable go <> back] 
        - Pick and Place: the user need to save the target holes (5 holes), this mode should input the index for pick and place, then press the `Start` button for execute the process.

---

### **Protocal : Address & Function**
---
#### **Register Address Table**

| Address   | Description   | Operation |
|---------- |----------     |---------- |
| 0x00      | Heartbear Protocol | Read/Write |  
| 0x01      | Base System Status [OK] | Write      | - 
| 0x02      | Gripper Status     [OK] | Read/Write | -
| 0x03      | Gripper Movement Status  [OK]  | Read/Write| -
| 0x04      | Gripper Movement Actual Status  [OK]  | Read | -
| 0x05      | Gripper Activate toggle [OK]    | Write | 
| 0x10      | Theta Moving Status [MAYBE] | Read |
| 0x11      | Theta Actual Position [OK]| Read |
| 0x12      | Theta Actual Velocity [OK]| Read |
| 0x13      | Theta Actual Acceleration [OK]| Read |
| 0x14      | Jog Mode (Command) [OK]   | Write |
| 0x15      | Test Mode (Performance/Precision) [OK]| Write|
| 0x16      | (Test)Performance - Speed  [OK] | Write |
| 0x17      | (Test)Performance - Accel  [OK] | Write |
| 0x18      | (Test)Precision - Init pos [OK] | Write |
| 0x19      | (Test)Precision - Target pos [OK]| Write |
| 0x20      | (Test)Precision - # Repeat (sign = unit) [OK] | Write  |
| 0x21-0x25 | Pick Hole #1-#5 (sign = direction) | Write |
| 0x26-0x30 | Place Hole #1-#5 (sign = direction) | Write | 
| 0x31      | Point to Point (unit)  [OK]  | Write | 
| 0x32      | Point to Point (value) [OK] | Write |
| 0x33      | Emergency status [OK]  | Read |
| 0x34      | Stop the process  [OK] | Write | 
---

### Data Format
#### 1. Base System Status (0x01) <span style="color:#2ea043;font-weight:bold">[DONE]</span>
Controls the robot’s high-level operating mode and system actions, such as homing, manual operation, or autonomous execution.

| Bit | Data in Binary | Data in Decimal | Description                                     |
| --- | -------------------- | ------- | ----------------------------------------------- |
| 0   | 0000 0000 0000 0001  | 1       | **Home Mode** – Execute homing         |
| 1   | 0000 0000 0000 0010  | 2       | **Manual Mode** – Entered Jog / manual control          |
| 2   | 0000 0000 0000 0100  | 4       | **Autonomous Mode** – Entered to automatic Mode|
| 3   | 0000 0000 0000 1000  | 8       | **Set Home** – Execute home setting    |
| 3   | 0000 0000 0001 0000  | 16       | **Test Mode** – Entered Test mode|


#### 2. Gripper Status (0x02) <span style="color:#2ea043;font-weight:bold">[DONE]</span>
Controls the gripper actuator (Grip / Release).

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0000 | 0 = Open | Gripper `Open` |
| 0   | 0000 0000 0000 0001 | 1 = Close | Gripper `Close` |
| 0   | 0000 0000 0000 0010 | 2 = Pick | Gripper `Pick` |
| 0   | 0000 0000 0000 0011 | 3 = Place | Gripper `Place` |


#### 3. Gripper Movement Status (0x03) <span style="color:#2ea043;font-weight:bold">[DONE]</span>
Commands the gripper linear movement direction.

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0000  | 0 = Up | Backward movement |
| 0   | 0000 0000 0000 0001   | 1 = Down  | Forward movement  |


#### 4. Gripper Movement Actual Status (0x04) <span style="color:#2ea043;font-weight:bold">[DONE]</span>

Reports the status of the three limit (reed) switches on the gripper mechanism.


> NOTE:  
reed#1 ON and reed#2 OFF == UP  
reed#1 OFF and reed#2 ON == DOWN  
reed#3 ON == CLOSE else UP

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0001 | 0 / 1 | Lead Switch 1 (0 = Off, 1 = On) |
| 1   | 0000 0000 0000 0010 | 0 / 2 | Lead Switch 2 (0 = Off, 1 = On) |
| 2   | 0000 0000 0000 0100 | 0 / 4 | Lead Switch 3 (0 = Off, 1 = On) |


#### 5. Gripper checkbox (0x05) <span style="color:#2ea043;font-weight:bold">[DONE]</span>

Gripper checkbox = enable / disable gripper actuation
- 'ON' -> Robot motion + gripper actions work
- 'OFF' -> Robot motion works, gripper does nothing

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0000 | 0 | gripper `OFF` |
| 0   | 0000 0000 0000 0001 | 1 | gripper `ON`  |


#### 6. Theta Moving Status (0x10) <span style="color:#2ea043;font-weight:bold">[DONE]</span>

Monitor the robot's internal state or which actions is currently performing.

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0001 | 1 | Homing |
| 1   | 0000 0000 0000 0010 | 2 |  Go Pick |
| 2   | 0000 0000 0000 0100 | 4 |  Go place |
| 3   | 0000 0000 0000 1000 | 8 |  Go Point |
<!-- | 4   | 0000 0000 0001 0000 | 16 |   | -->



#### 7. Position / Speed / Accelation (0x11 to 0x13) <span style="color:#2ea043;font-weight:bold">[DONE]</span>
Moniter the robot's actual position, speed, accelation. Must contain only two decimal place, before sending the values to the `Base System`, multiply the actual value to 10 (Base_system_value = Actual_value * 10)

> Example: If the value of the position you want to send is '123.4', multiply by 10 to get '1234', and send this value to the address z-axis Actual position (0x11). This will appear in Base-system as '123.4'  



<!-- #### 8. Pick order(0x21), Place order(0x22) <span style="color:#d73a49;font-weight:bold">[NOT YET]</span>
The order of pick and place sent from the Base system to the robot will correspond to the pick and place order displayed in GUI. 



#### 9. Emergency status (0x40) <span style="color:#d73a49;font-weight:bold">[NOT YET]</span>
This receive the `Emergency button state` from the robot
| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0000 | 0 | Emergency `Did not pressed`|
| 0   | 0000 0000 0000 0001 | 1 | Emergency `Pressed`  |

#### 10. Stop the process (0x41) <span style="color:#d73a49;font-weight:bold">[NOT YET]</span>
Stop the robot's process.

| Bit | Data in Binary | Data in Decimal | Meaning |
| ----- | ----- | ----- | ----- |
| 0   | 0000 0000 0000 0000 | 0 | Robot's run normally  |
| 0   | 0000 0000 0000 0001 | 1 | Stop the process      | -->