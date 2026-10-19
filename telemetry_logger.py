import threading
from collections import deque


class TelemetryLogger:
    def __init__(self):
        self.history = deque(maxlen=3600) #Какие данные может хранить deque?
        self.lock = threading.Lock() #Зачем лок?

    def add(self, timestamp, temperature, current, soc):
        point = {
            "timestamp": timestamp,
            "temperature": temperature,
            "current": current,
            "soc": soc
        }

        with self.lock:
            self.history.append(point)

    def latest(self):
        with self.lock:
            if not self.history:
                return None
            return self.history[-1].copy() #Обязательно ли копирование?


    def last_seconds(self, seconds):
        with self.lock:
            if not self.history:
                return []

            current_time = self.history[-1]["timestamp"] # Избегаем повторного захвата того же threading.Lock
            start_time = current_time - seconds
            result = []
            for point in self.history:
                if point["timestamp"] >= start_time:
                    result.append(point.copy())
        return result

    def average_current(self, seconds):
        window = self.last_seconds(seconds)

        if not window:
            return None

        current_overall = 0
        for point in window:
            current_overall += point["current"]

        return current_overall/len(window)

    def __len__(self):
        with self.lock:
            return len(self.history)
