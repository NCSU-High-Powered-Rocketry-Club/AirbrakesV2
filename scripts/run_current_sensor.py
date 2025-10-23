import time, board, busio
from adafruit_ina219 import INA219

i2c = busio.I2C(board.SCL, board.SDA)
ina = INA219(i2c, addr=0x45)  # change if your DIP address differs

while True:
    print(f"Current: {ina.current:.3f} mA")   # also: ina.bus_voltage (V), ina.power (mW)
    time.sleep(0.5)
