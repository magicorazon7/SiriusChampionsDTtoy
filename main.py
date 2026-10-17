import time

from modbus_reader import ModbusReader

MODBUS_IP = "127.0.0.1"
MODBUS_PORT = 502

reader = ModbusReader(MODBUS_IP, MODBUS_PORT)

if reader.connect(): #проверка подключения к серверу при помощи метода connect()
    try:
        while True:
            data = reader.read()

            if data is not None:
                print(
                    "Modbus read data (T, I, SOC):",
                    data["temperature"],
                    data["current"],
                    data["soc"]
                )

            time.sleep(1)

    finally:
        reader.close()