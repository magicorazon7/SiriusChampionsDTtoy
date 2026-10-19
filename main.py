import threading
import time
import json
from telemetry_logger import TelemetryLogger

from modbus_reader import ModbusReader

MODBUS_IP = "127.0.0.1"
MODBUS_PORT = 502

reader = ModbusReader(MODBUS_IP, MODBUS_PORT)
logger = TelemetryLogger()

def save_telemetry(data, elapsed_time):
    telemetry = {
        "time": round(elapsed_time, 2),
        "temperature": round(data["temperature"], 2),
        "current": round(data["current"], 2),
        "soc": round(data["soc"], 2),
    }
    with open("telemetry.json", "w", encoding="utf-8") as file:
        json.dump(telemetry, file, indent=4)

def collect_telemetry(reader, logger, start_time, stop_event):
    while not stop_event.is_set():
        data = reader.read()

        if data is not None:
            elapsed_time = time.monotonic() - start_time

            logger.add(
                timestamp=elapsed_time,
                temperature=data["temperature"],
                current=data["current"],
                soc=data["soc"]
            )

            save_telemetry(data, elapsed_time)

            print(
                f"t={elapsed_time:.1f} с | "
                f"T={data['temperature']:.2f} °C | "
                f"I={data['current']:.1f} A | "
                f"SOC={data['soc']:.1f} %"
            )

        stop_event.wait(1)


if not reader.connect():
    exit()

start_time = time.monotonic()
stop_event = threading.Event()

collector_thread = threading.Thread(
    target=collect_telemetry,
    args=(reader, logger, start_time, stop_event),
)

collector_thread.start()

try:
    while True:
        time.sleep(1)

finally:
    stop_event.set()
    collector_thread.join(timeout=2)
    reader.close()