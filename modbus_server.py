import threading
import time
import tkinter as tk

from pymodbus.server import StartTcpServer
from pymodbus.datastore import (
    ModbusSlaveContext,
    ModbusServerContext,
    ModbusSequentialDataBlock
)

from device_simulator import BatterySimulator

HOST = "127.0.0.1"
PORT = 502

sim = BatterySimulator()

# ---------- Modbus datastore ----------

store = ModbusSlaveContext(
    zero_mode=True,
    hr=ModbusSequentialDataBlock(0, [0] * 3)
)

context = ModbusServerContext(
    slaves=store,
    single=True
)

# ---------- Обновление Modbus-регистров ----------

def update_registers():
    while True:
        T, I, SOC = sim.step()

        context[0].setValues(
            3,
            0,
            [
                int(T * 100),
                int(I * 10),
                int(SOC * 10)
            ]
        )
        registers = context[0].getValues(3, 0, count=3)
        # print("Raw registers(T,I,SOC): ", registers)
        # print("Corrected registers(T,I,SOC): ",registers[0]/100," ", registers[1]/10," ",registers[2]/10," ")

        time.sleep(1)


# ---------- Modbus server ----------

def run_modbus_server():
    print(f"Modbus TCP server started on {HOST}:{PORT}")

    StartTcpServer(
        context=context,
        address=(HOST, PORT)
    )


# ---------- GUI ----------

def change_r_th(value):
    sim.R_th = float(value)

    r_th_label.config(
        text=f"R_th объекта = {sim.R_th:.3f} К/Вт"
    )


def create_gui():
    global r_th_label

    root = tk.Tk()
    root.title("Battery Simulator Control")
    root.geometry("420x180")

    title = tk.Label(
        root,
        text="Параметры виртуальной батареи",
        font=("Arial", 14, "bold")
    )
    title.pack(pady=10)

    r_th_label = tk.Label(
        root,
        text=f"R_th объекта = {sim.R_th:.3f} К/Вт",
        font=("Arial", 12)
    )
    r_th_label.pack()

    slider = tk.Scale(
        root,
        from_=0.07,
        to=0.15,
        resolution=0.01,
        orient=tk.HORIZONTAL,
        length=350,
        command=change_r_th
    )

    slider.set(sim.R_th)
    slider.pack(pady=10)

    root.mainloop()


# ---------- Start ----------

if __name__ == "__main__":
    register_thread = threading.Thread(
        target=update_registers,
        daemon=True
    )

    server_thread = threading.Thread(
        target=run_modbus_server,
        daemon=True
    )

    register_thread.start()
    server_thread.start()

    create_gui()