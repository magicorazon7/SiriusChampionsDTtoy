class Calibrator:
    def __init__(self, twin):
        self.twin = twin

    def calculate_mismatch(self, history, r_th):
        n = 5

        if len(history) < n:
            return None

        temp_init = sum(point["temperature"] for point in history[:n]) / n
        temp_real_end = sum(point["temperature"] for point in history[-n:]) / n

        soc_init = history[0]["soc"]
        avg_current = sum(point["current"] for point in history) / len(history)

        delta_real = temp_real_end - temp_init

        temperature_result, _ = self.twin.run_model(
            thermal_res=r_th,
            temp_batt=temp_init,
            current=avg_current,
            soc_init=soc_init
        )

        model_temp_end = temperature_result.iloc[-1]
        delta_model = model_temp_end - temp_init

        error = abs(delta_model - delta_real)

        print("\nРассогласование объекта и модели:")
        print(f"ΔT объекта = {delta_real:.4f} °C")
        print(f"ΔT модели  = {delta_model:.4f} °C")
        print(f"Ошибка     = {error:.5f} °C")

        return error