class Calibrator:
    def __init__(self, twin, candidates):
        self.twin = twin
        self.candidates = candidates

    def calibrate(self, history):
        n = 5

        if len(history) < n:
            return None, None

        temp_init = sum(point["temperature"] for point in history[:n]) / n
        temp_real_end = sum(point["temperature"] for point in history[-n:]) / n

        soc_init = history[0]["soc"]
        avg_current = sum(point["current"] for point in history) / len(history)

        delta_real = temp_real_end - temp_init

        best_r_th = None
        best_error = float("inf")

        print("\n--- GRID SEARCH ---")
        print(f"T_start = {temp_init:.3f} °C")
        print(f"T_end = {temp_real_end:.3f} °C")
        print(f"ΔT объекта = {delta_real:.4f} °C")
        print(f"I_avg = {avg_current:.2f} A")

        for r_th in self.candidates:
            temperature_result, _ = self.twin.run_model(
                thermal_res=r_th,
                temp_batt=temp_init,
                current=avg_current,
                soc_init=soc_init
            )

            model_temp_end = temperature_result.iloc[-1]
            delta_model = model_temp_end - temp_init

            error = abs(delta_model - delta_real)

            print(
                f"R_th={r_th:.3f} К/Вт | "
                f"ΔT_model={delta_model:.4f} °C | "
                f"error={error:.5f} °C"
            )

            if error < best_error:
                best_error = error
                best_r_th = r_th

        print(
            f"Лучший результат: "
            f"R_th={best_r_th:.3f} К/Вт | "
            f"error={best_error:.5f} °C"
        )

        return best_r_th, best_error