import platform 
import struct
import time
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.client import ModbusTcpClient

# ============================= Congif Computer port here  ==============================

device_port = "COM3"
# example: for os -> device_port = "/dev/cu.usbmodem14103"
#          for window -> device_port = "COM3"
# =======================================================================================



class Binary():
    """
    Binary Class
    """
    def decimal_to_binary(self, decimal_num):
        """
        This function converts base 10 to base 2
        """
        binary_num = ""
        while decimal_num > 0:
            binary_num = str(decimal_num % 2) + binary_num
            decimal_num = decimal_num // 2
        # Fill to 16 digits with 0
        if len(binary_num) < 16:
            binary_num = "0"*(16-len(binary_num)) + binary_num
        return binary_num
        
    def binary_to_decimal(self, binary_num):
        """
        This function converts base 2 to base 10
        """
        decimal_num = 0
        for i in range(len(binary_num)):
            decimal_num += int(binary_num[i]) * (2 ** (len(binary_num)-i-1))
        return decimal_num
    
    def binary_crop(self, digit, binary_num):
        """
        This function crops the last n digits of the binary number
        """
        return binary_num[len(binary_num)-digit:]

    def binary_twos_complement(self, number):
        """
        This functions converts the (negative) number to its 16-bit two's complement representation
        """
        if number < 0:
            number = (1 << 16) + number  # Adding 2^16 to the negative number
        return number
    
    def binary_reverse_twos_complement(self, number):
        """
        This functions converts the 16-bit two's complement number back to its original signed representation 
        """
        if number & (1 << 15):  # Check if the most significant bit is 1
            number = number - (1 << 16)  # Subtract 2^16 from the number
        return number


class Protocol(Binary):
    """
    Protocol Theta robot Class
    """
    def __init__(self):
        self.os = platform.platform()[0].upper()
        if self.os == 'M': #Mac
            self.port = device_port
        elif self.os == 'W': #Windows        
            self.port = device_port

        # Modbus Client
        self.usb_connect = False
        self.usb_connect_before = False

        # Modbus TCP Client
        self.slave_address = False
        self.register = []

        # Routine
        self.routine_normal = True

        # Base system status (0x01)
        self.base_system_status_register = 0b0000
        
        # Gripper status (0x02) -- 0: Release, 1: Grip
        self.gripper_status = "0"
        
        # Gripper Movement status (0x03) 0: Backward, 1: Forward
        self.gripper_moving_status = "0"

        # Gripper Movement Actual Status (0x04) 
        self.gripper_actual_reed1 = "0"  
        self.gripper_actual_reed2 = "0"
        self.gripper_actual_reed3 = "0"

        # Gripper Checkbox (0x05) -- 0: Disable, 1: Enable
        self.gripper_checkbox = "0"

        # Thetha Moving Status (0x10)
        self.moving_status = "Idle"
        self.moving_status_previous = "Idle"

        # Theta Moving Status (0x11 - 0x13) 
        self.theta_actual_pos = 0.0
        self.thata_actual_speed = 0.0
        self.theta_actual_accel = 0.0

        # Pick and Place Status (0x20)
        self.shelve_1 = 0
        self.shelve_2 = 0
        self.shelve_3 = 0
        self.shelve_4 = 0
        self.shelve_5 = 0

        # Emergency Stop Status (0x40) -- 0: Normal, 1: Emergency Stop
        self.emergency_stop_status = "0" 

        # Stop the process (0x41) -- 0: Normal, 1: Stop
        self.stop_process = "0"

        # Modbus Client
        self.client = ModbusClient(method='rtu', port=self.port, stopbits=1, bitsize=8, parity='E', baudrate=19200)
        print("[Protocol] Operating System:", self.os, "| Port:", self.port, self.client.connect())

    # ============================= Heartbeat Functions (0x00) =============================
    def heartbeat(self):
        if self.read_heartbear() == 1111:
            self.write_heartbeat()
            print("[Protocol] Heartbeat successful")
            return True
        else:
            print("[Protocol] Heartbeat failed")
            return False

    def read_heartbear(self):
        try:
            hearbeat_value = self.client.read_holding_registers(address=0x00, count=1, slave=self.slave_address).registers
        except Exception as e:
            print(f"[Protocol] Error reading heartbeat: {e}")
            return 0    
        return hearbeat_value[0]        

    def write_heartbeat(self):
        try:
            self.client.write_register(address=0x00, value=18537, slave=self.slave_address)
            print("[Protocol] Write Heartbeat: 18537")
            self.usb_connect = True
        except:
            self.usb_connect = False

    # ============================= Routine Function =============================
    def routine(self):
        try: 
            self.register = self.client.read_holding_registers(address=0x00, count=66, slave=self.slave_address)
            # IMPORTANT: handle Modbus errors
            if self.register is None or self.register.isError():
                print(f"[Protocol] read_holding_registers error: {self.register}")
                self.routine_normal = False
                return
            print(f"[Protocol] Register Values: {self.register.registers[:]}")

            # self.write_gripper_command("Place") # (0x02)
            # self.write_gripper_movement("Forward")  # (0x03)
            # self.write_gripper_checkbox("Enable")  # (0x05)

            # print(self.moving_status)

            # Routine for reading registers
            self.read_gripper_actual_status()   # gripper status (0x02 - 0x04)
            self.read_theta_moving_status()     # theta moving status (0x10)
            self.read_theta_actual_status()     # theta actual status (0x11 - 0x13)
            self.read_emergency_stop_status()   # emergency stop status (0x40)

            # print(f"[Protocol] Gripper Status: {self.gripper_status} | Gripper Movement Status: {self.gripper_moving_status}")

            # print(f"[Protocol] Gripper Status: {self.gripper_status} | Gripper Movement Status: {self.gripper_moving_status} | "
            #         f"Gripper Actual Reed Status: {self.gripper_actual_reed1}, {self.gripper_actual_reed2}, {self.gripper_actual_reed3} | "
            #         f"Theta Moving Status: {self.moving_status} | Theta Actual Position: {self.theta_actual_pos} | "
            #         f"Theta Actual Speed: {self.thata_actual_speed} | Theta Actual Accel: {self.theta_actual_accel} | "
            #         f"Emergency Stop Status: {self.emergency_stop_status}")

            # self.heartbeat()  # Write heartbeat at the end of the routine
            
            self.routine_normal = True
        except Exception as e:
            print(f"[Protocol] Error in routine: {e}")
            self.routine_normal = False


    # ============================= Write Register Functions (0x01) =============================
    def write_base_system_status(self, command):
        if command == 'Home':
            self.base_system_status_register = 0b0001   
        elif command == 'Jog':
            self.base_system_status_register = 0b0010
        elif command == 'Auto':
            self.base_system_status_register = 0b0100
        # else:
        #     self.base_system_status_register = 0b0000
        self.client.write_register(address=0x01, value=self.base_system_status_register, slave=self.slave_address)
        print(f"[Protocol] Write Base System Status: {command} | Register: {self.base_system_status_register}")

    # ============================= Write Register Functions (0x02) =============================
    def write_gripper_command(self, command):
        if command == 'Release':
            self.gripper_command_register = 0b0000   
        elif command == 'Grip':
            self.gripper_command_register = 0b0001
        elif command == 'Pick':
            self.gripper_command_register = 0b0010
        elif command == 'Place':
            self.gripper_command_register = 0b0011
        self.client.write_register(address=0x02, value=self.gripper_command_register, slave=self.slave_address)
        print(f"[Protocol] Write Gripper Command: {command} | Register: {self.gripper_command_register}")

    # ============================= Write Register Functions (0x03) =============================
    def write_gripper_movement(self, command):
        if command == 'Backward':
            self.gripper_movement_register = 0b0000   
        elif command == 'Forward':
            self.gripper_movement_register = 0b0001
        self.client.write_register(address=0x03, value=self.gripper_movement_register, slave=self.slave_address)
        print(f"[Protocol] Write Gripper Movement: {command} | Register: {self.gripper_movement_register}")

    # ============================= Read Register Functions (0x02-0x04) =============================
    def read_gripper_actual_status(self):
        gripper_state_binary = self.binary_to_decimal(self.binary_crop(4, self.decimal_to_binary(self.register.registers[0x02])))
        gripper_movement_binary = self.binary_crop(4, self.decimal_to_binary(self.register.registers[0x03]))[::-1]
        
        # Reed switch status
        gripper_actual_status_binary = self.binary_crop(4, self.decimal_to_binary(self.register.registers[0x04]))[::-1]
        # print(f"[Protocol] Gripper Actual Status Binary: {gripper_actual_status_binary}")

        self.gripper_status = gripper_state_binary  # Gripper Status
        self.gripper_moving_status = gripper_movement_binary[0]  # Gripper Movement Status

        self.gripper_actual_reed1 = gripper_actual_status_binary[0]  # Reed Switch 1 Status
        self.gripper_actual_reed2 = gripper_actual_status_binary[1]  # Reed Switch 2 Status
        self.gripper_actual_reed3 = gripper_actual_status_binary[2]  # Reed Switch 3 Status

    # ============================= Write Register Functions (0x05) =============================
    def write_gripper_checkbox(self, command):
        if command == 'Disable':
            self.gripper_checkbox_register = 0b0000   
        elif command == 'Enable':
            self.gripper_checkbox_register = 0b0001
        self.client.write_register(address=0x05, value=self.gripper_checkbox_register, slave=self.slave_address)
        print(f"[Protocol] Write Gripper Checkbox: {command} | Register: {self.gripper_checkbox_register}")

    # ============================= Read Register Functions (0x10) =============================
    def read_theta_moving_status(self):
        self.moving_status_previous = self.moving_status
        moving_status_binary = self.binary_crop(6, self.decimal_to_binary(self.register.registers[0x10]))[::-1]
    
        # moving_status_binary = ['0', '1','0','0']
        if moving_status_binary[0] == '1':
            self.moving_status = "Homing"
        elif moving_status_binary[1] == '1':
            self.moving_status = "Go Pick"
        elif moving_status_binary[2] == '1':
            self.moving_status = "Go Place"
        elif moving_status_binary[3] == '1':
            self.moving_status = "Go Point"
        else:
            self.moving_status = "Idle"

    # ============================= Read Register Functions (0x11 - 0x13) =============================
    def read_theta_actual_status(self):
        self.theta_actual_pos = self.binary_reverse_twos_complement(self.register.registers[0x11]) / 10.0
        self.theta_actual_speed = self.register.registers[0x12] / 10.0
        self.theta_actual_accel = self.register.registers[0x13] / 10.0

    # ============================= Write Register Functions (0x30) =============================
    # Manual Movement - Goal Point
    def write_goal_point(self, mode='', value=None):
        if mode == 'Index':
            self.goal_point_register = self.binary_twos_complement(int(value))
        elif mode == 'Position':
            self.goal_point_register = self.binary_twos_complement(int(value * 10))
        self.client.write_register(address=0x30, value=self.goal_point_register, slave=self.slave_address)

    # ============================= Write Register Functions (0x31) =============================
    def write_point_to_point(self, mode='', value=None, repeat=0):
        self.write_goal_point(mode, value)
        self.client.write_register(address=0x31, value=repeat, slave=self.slave_address)

    def read_emergency_stop_status(self):
        emergency_stop_binary = self.binary_crop(4, self.decimal_to_binary(self.register.registers[0x40]))[::-1]
        self.emergency_stop_status = emergency_stop_binary[0]  # Emergency Stop Status

    def write_stop_process(self, command):
        if command == 'Normal':
            self.stop_process_register = 0b0000   
        elif command == 'Stop':
            self.stop_process_register = 0b0001
        self.client.write_register(address=0x41, value=self.stop_process_register, slave=self.slave_address)
        print(f"[Protocol] Write Stop Process: {command} | Register: {self.stop_process_register}")
