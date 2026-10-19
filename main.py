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

def save_forecast(state,avg_current,final_temperature,final_soc,time_to_overheat,r_th):
    forecast = {
        "timestamp": time.time(),
        "current_temp": round(state["temperature"], 2),
        "current_soc": round(state["soc"], 2),
        "avg_current": round(avg_current, 2),
        "horizon_sec": HORIZON_SEC,
        "predicted_temp": round(final_temperature, 2),
        "predicted_soc": round(final_soc, 2),
        "time_to_overheat_sec": time_to_overheat,
        "r_th": round(r_th, 4)
    }
    with open("forecast.json", "w", encoding="utf-8") as file:json.dump(forecast, file, indent=4)

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

def find_time_to_overheat(temperature_series, limit):
    for t_ms, temperature in temperature_series.items():
        if temperature >= limit:
            return t_ms / 1000.0

    return -1

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

                time_to_overheat = find_time_to_overheat(
                    temperature_result,
                    OVERHEAT_TEMP
                )

                save_forecast(
                    state=state,
                    avg_current=i_avg,
                    final_temperature=final_temperature,
                    final_soc=final_soc,
                    time_to_overheat=time_to_overheat,
                    r_th=current_r_th
                )

            last_prediction_time = elapsed_time

        time.sleep(0.2)

finally:
    stop_event.set()
    collector_thread.join(timeout=2)
    reader.close()