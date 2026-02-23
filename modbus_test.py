import tkinter as tk
from tkinter import ttk
from pymodbus.client import ModbusSerialClient


class ModbusUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Modbus RTU Tester 101")
        self.geometry("600x320")

        frm = ttk.Frame(self, padding=10)
        frm.pack(fill="both", expand=True)

        # Connection
        ttk.Label(frm, text="COM Port").grid(row=0, column=0, sticky="w")
        self.port_entry = ttk.Entry(frm)
        self.port_entry.insert(0, "COM3")
        self.port_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(frm, text="Baud").grid(row=1, column=0, sticky="w")
        self.baud_entry = ttk.Entry(frm)
        self.baud_entry.insert(0, "19200")
        self.baud_entry.grid(row=1, column=1, sticky="ew")

        ttk.Label(frm, text="Parity (N/E/O)").grid(row=2, column=0, sticky="w")
        self.parity_entry = ttk.Entry(frm)
        self.parity_entry.insert(0, "E")
        self.parity_entry.grid(row=2, column=1, sticky="ew")

        # Slave / address / value
        ttk.Label(frm, text="Slave ID").grid(row=3, column=0, sticky="w")
        self.slave_entry = ttk.Entry(frm)
        self.slave_entry.insert(0, "21")
        self.slave_entry.grid(row=3, column=1, sticky="ew")

        ttk.Label(frm, text="Register Address").grid(row=4, column=0, sticky="w")
        self.addr_entry = ttk.Entry(frm)
        self.addr_entry.insert(0, "0")
        self.addr_entry.grid(row=4, column=1, sticky="ew")

        ttk.Label(frm, text="Value (int)").grid(row=5, column=0, sticky="w")
        self.value_entry = ttk.Entry(frm)
        self.value_entry.insert(0, "555")
        self.value_entry.grid(row=5, column=1, sticky="ew")

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")

        ttk.Button(btns, text="Read", command=self.read_register).pack(side="left", padx=5)
        ttk.Button(btns, text="Write", command=self.write_register).pack(side="left", padx=5)

        # Log
        self.log_box = tk.Text(frm, height=8)
        self.log_box.grid(row=7, column=0, columnspan=2, sticky="nsew")

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(7, weight=1)

    def log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def connect(self):
        port = self.port_entry.get().strip()
        baud = int(self.baud_entry.get())
        parity = self.parity_entry.get().strip().upper()
        if parity not in ("N", "E", "O"):
            self.log(f"[ERROR] Invalid parity: {parity}. Use N, E, or O.")
            return None

        client = ModbusSerialClient(
            port=port,
            baudrate=baud,
            parity=parity,
            stopbits=1,
            bytesize=8,
            timeout=1,
        )

        if not client.connect():
            self.log(f"[ERROR] Cannot connect to {port}")
            return None

        return client

    def read_register(self):
        client = self.connect()
        if not client:
            return

        try:
            slave = int(self.slave_entry.get())
            address = int(self.addr_entry.get())

            result = client.read_holding_registers(address=address, count=1, slave=slave)

            if result is None:
                self.log("[ERROR] Read returned None (no response).")
                return
            if hasattr(result, "isError") and result.isError():
                self.log(f"[ERROR] Read error: {result}")
                return
            if not hasattr(result, "registers"):
                self.log(f"[ERROR] Read failed: {type(result).__name__}: {result}")
                return

            raw_value = result.registers[0]
            signed_value = raw_value if raw_value < 32768 else raw_value - 65536
            self.log(f"[DONE] Read sl={slave} addr={address} "
                     f"-> signed:{signed_value} | raw:{raw_value}")
        
        finally:
            client.close()

    def write_register(self):
        client = self.connect()
        if not client:
            return

        try:
            slave = int(self.slave_entry.get())
            address = int(self.addr_entry.get())
            value = int(self.value_entry.get())
        
            # Send as 16-bit unsigned register
            value_16 = value & 0xFFFF

            result = client.write_register(address=address, value=value_16, slave=slave)

            if result is None:
                self.log("[ERROR] Write returned None (no response).")
                return
            if hasattr(result, "isError") and result.isError():
                self.log(f"[ERROR] Write error: {result}")
                return

            self.log(
                f"[DONE] Write sl={slave} addr={address} "
                f"<- signed:{value} | raw:{value_16} | hex:0x{value_16:04X}"
)
        finally:
            client.close()


if __name__ == "__main__":
    app = ModbusUI()
    app.mainloop()