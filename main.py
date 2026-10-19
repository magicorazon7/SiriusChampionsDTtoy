import threading
import time
import json

from telemetry_logger import TelemetryLogger
from modbus_reader import ModbusReader
from repeat_twin import RepeatTwin

MODBUS_IP = "127.0.0.1"
MODBUS_PORT = 502

PREDICTION_INTERVAL = 30
PREDICTION_WINDOW = 30
HORIZON_SEC = 900

MODEL_R_TH_INITIAL = 0.11
OVERHEAT_TEMP = 42.0
REPEAT_API_KEY = "ваш апи ключ"
REPEAT_PROJECT_ID = "айди вашего проекта"

reader = ModbusReader(MODBUS_IP, MODBUS_PORT)
logger = TelemetryLogger()
forecast_twin = RepeatTwin(api_key=REPEAT_API_KEY,project_id=REPEAT_PROJECT_ID,interval_sec=HORIZON_SEC)

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
    args=(reader, logger, start_time, stop_event)
)

collector_thread.start()

try:
    last_prediction_time = 0
    current_r_th = MODEL_R_TH_INITIAL

    while True:
        elapsed_time = time.monotonic() - start_time

        if elapsed_time - last_prediction_time >= PREDICTION_INTERVAL:
            state = logger.latest()
            i_avg = logger.average_current(PREDICTION_WINDOW)

            if state is not None and i_avg is not None:
                temperature_result, soc_result = forecast_twin.run_model(
                    thermal_res=current_r_th,
                    temp_batt=state["temperature"],
                    current=i_avg,
                    soc_init=state["soc"]
                )

                final_temperature = temperature_result.iloc[-1]
                final_soc = soc_result.iloc[-1]

                print("\nРезультаты расчета модели:")
                print(f"Temp in 15 min = {final_temperature} °C")
                print(f"SOC in 15 min = {final_soc} %")

            last_prediction_time = elapsed_time

        time.sleep(0.2)

finally:
    stop_event.set()
    collector_thread.join(timeout=2)
    reader.close()