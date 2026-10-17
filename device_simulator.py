import random
import time

class BatterySimulator:
    def __init__(self, R_int=0.1, C_th=990*250, R_th=0.11, T_amb=20.0, T_batt = 39, Cap = 65, SOC = 90.0):
        self.R_int = R_int          # внутреннее сопротивление, Ом
        self.C_th = C_th            # теплоёмкость, Дж/К
        self.R_th = R_th            # термическое сопротивление, К/Вт
        self.T_amb = T_amb          # температура окружающей среды, °C
        self.T = T_batt              # текущая температура батареи, °C
        self.Cap = Cap
        self.SOC = SOC
        self.time = 0.0             # симуляционное время, секунды
        self.current = 80          # текущий ток, А (начальное значение)

    def step(self, dt=1.0):
        # Генерируем изменение тока
        self.current += random.uniform(-0.1, 0.1)
        self.current = max(0.1, min(100, self.current))

        # Тепловая модель
        P_heat = self.current**2 * self.R_int
        dT = (P_heat - (self.T - self.T_amb) / self.R_th) / self.C_th * dt
        self.T += dT

        # Изменение SOC
        if self.Cap > 0:
            dSOC = - (self.current * dt) / (self.Cap * 3600) * 100   # в процентах
            self.SOC += dSOC
            self.SOC = max(0, min(100, self.SOC))   # ограничиваем

        # Шум
        T_noisy = self.T + random.gauss(0, 0.005)
        I_noisy = self.current + random.gauss(0, 0.05)

        self.time += dt
        return T_noisy, I_noisy, self.SOC   # возвращаем и SOC

if __name__ == "__main__":
    sim = BatterySimulator()
    while True:
        T, I, SOC = sim.step()
        print("Температура, ток и уровень заряда: ",T,I,SOC)
        time.sleep(1)