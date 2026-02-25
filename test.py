import tkinter as tk
from tkinter import ttk
from pymodbus.client import ModbusSerialClient


class ModbusUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Modbus RTU Tester 101")
        self.geometry("650x380")

        self.client = None              # persistent client
        self.poll_job = None            # after() job id
        self.poll_ms = 200              # default polling interval (ms)

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

        ttk.Label(frm, text="Poll interval (ms)").grid(row=6, column=0, sticky="w")
        self.poll_entry = ttk.Entry(frm)
        self.poll_entry.insert(0, str(self.poll_ms))
        self.poll_entry.grid(row=6, column=1, sticky="ew")

        # Buttons
        btns = ttk.Frame(frm)
        btns.grid(row=7, column=0, columnspan=2, pady=8, sticky="ew")

        ttk.Button(btns, text="Connect", command=self.connect_persistent).pack(side="left", padx=5)
        ttk.Button(btns, text="Disconnect", command=self.disconnect_persistent).pack(side="left", padx=5)
        ttk.Button(btns, text="Read Once", command=self.read_register_once).pack(side="left", padx=5)
        ttk.Button(btns, text="Write Once", command=self.write_register_once).pack(side="left", padx=5)

        ttk.Separator(frm).grid(row=8, column=0, columnspan=2, sticky="ew", pady=6)

        ttk.Button(btns, text="Start Poll", command=self.start_poll).pack(side="left", padx=5)
        ttk.Button(btns, text="Stop Poll", command=self.stop_poll).pack(side="left", padx=5)

        # Log
        self.log_box = tk.Text(frm, height=10)
        self.log_box.grid(row=9, column=0, columnspan=2, sticky="nsew")

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(9, weight=1)

        # ensure clean shutdown
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    # ---------- Persistent connect/disconnect ----------
    def connect_persistent(self):
        if self.client is not None:
            self.log("[INFO] Already connected.")
            return

        port = self.port_entry.get().strip()
        baud = int(self.baud_entry.get())
        parity = self.parity_entry.get().strip().upper()
        if parity not in ("N", "E", "O"):
            self.log(f"[ERROR] Invalid parity: {parity}. Use N, E, or O.")
            return

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
            return

        self.client = client
        self.log(f"[DONE] Connected to {port} (baud={baud}, parity={parity})")

    def disconnect_persistent(self):
        self.stop_poll()
        if self.client:
            self.client.close()
            self.client = None
            self.log("[DONE] Disconnected.")

    # ---------- Single-shot read/write ----------
    def read_register_once(self):
        if not self.client:
            self.connect_persistent()
        if not self.client:
            return
        self._read_and_log()

    def write_register_once(self):
        if not self.client:
            self.connect_persistent()
        if not self.client:
            return

        slave = int(self.slave_entry.get())
        address = int(self.addr_entry.get())
        value = int(self.value_entry.get())
        value_16 = value & 0xFFFF

        result = self.client.write_register(address=address, value=value_16, slave=slave)

        if result is None:
            self.log("[ERROR] Write returned None (no response).")
            return
        if hasattr(result, "isError") and result.isError():
            self.log(f"[ERROR] Write error: {result}")
            return

        self.log(f"[DONE] Write sl={slave} addr={address} <- signed:{value} | raw:{value_16} | hex:0x{value_16:04X}")

    # ---------- Polling loop (timer) ----------
    def start_poll(self):
        if self.poll_job is not None:
            self.log("[INFO] Poll already running.")
            return

        # read interval
        try:
            self.poll_ms = max(50, int(self.poll_entry.get()))
        except ValueError:
            self.log("[ERROR] Poll interval must be an integer (ms).")
            return

        if not self.client:
            self.connect_persistent()
        if not self.client:
            return

        self.log(f"[DONE] Start polling every {self.poll_ms} ms")
        self._poll_tick()

    def _poll_tick(self):
        # do one read
        if self.client:
            self._read_and_log()

        # schedule next tick
        self.poll_job = self.after(self.poll_ms, self._poll_tick)

    def stop_poll(self):
        if self.poll_job is not None:
            self.after_cancel(self.poll_job)
            self.poll_job = None
            self.log("[DONE] Poll stopped.")

    def _read_and_log(self):
        slave = int(self.slave_entry.get())
        address = int(self.addr_entry.get())

        result = self.client.read_holding_registers(address=address, count=1, slave=slave)

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
        self.log(f"[READ] sl={slave} addr={address} -> signed:{signed_value} | raw:{raw_value} | hex:0x{raw_value:04X}")

    def on_close(self):
        self.disconnect_persistent()
        self.destroy()


if __name__ == "__main__":
    app = ModbusUI()
    app.mainloop()