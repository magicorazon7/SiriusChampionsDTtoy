from pymodbus.client import ModbusTcpClient


class ModbusReader:
    def __init__(self, ip="127.0.0.1", port=502):
        self.ip = ip
        self.port = port
        self.client = ModbusTcpClient(self.ip, port=self.port)

    def connect(self):
        if self.client.connect():
            print(f"Подключение к Modbus {self.ip}:{self.port} установлено")
            return True

        print("Ошибка подключения к Modbus")
        return False

    def read(self):
        rr = self.client.read_holding_registers(0, 3)

        if rr.isError():
            return None

        temperature = rr.registers[0] / 100.0
        current = rr.registers[1] / 10.0
        soc = rr.registers[2] / 10.0

        return {
            "temperature": temperature,
            "current": current,
            "soc": soc
        }

    def close(self):
        self.client.close()