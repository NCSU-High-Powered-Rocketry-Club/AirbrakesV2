#!/usr/bin/env python3
"""
BMP180 Altitude Reader for Raspberry Pi
---------------------------------------
Continuously reads altitude (in meters) from a BMP180 sensor over I2C.

Wiring (3.3 V logic only!):
  3V3 → VCC
  GND → GND
  SDA → GPIO2 (SDA1)
  SCL → GPIO3 (SCL1)

Enable I2C:
  sudo raspi-config  →  Interface Options → I2C → Enable → reboot

Install dependencies:
  pip install smbus2
"""

import time
from smbus2 import SMBus

BMP180_ADDR = 0x77

# Registers
REG_CALIB_START = 0xAA
REG_CONTROL     = 0xF4
REG_RESULT      = 0xF6

# Commands
CMD_TEMP     = 0x2E
CMD_PRESSURE = 0x34  # + (oss << 6)

DEFAULT_OSS = 0  # Oversampling: 0..3
CONV_WAIT_S = {0: 0.005, 1: 0.008, 2: 0.014, 3: 0.026}


def _to_s16(msb, lsb):
    val = (msb << 8) | lsb
    if val > 32767:
        val -= 65536
    return val


def _to_u16(msb, lsb):
    return (msb << 8) | lsb


class BMP180:
    def __init__(self, bus, addr=BMP180_ADDR, oss=DEFAULT_OSS):
        if oss < 0:
            oss = 0
        if oss > 3:
            oss = 3
        self.bus = bus
        self.addr = addr
        self.oss = oss
        self._read_calibration()

    def _read_calibration(self):
        data = self.bus.read_i2c_block_data(self.addr, REG_CALIB_START, 22)
        self.AC1 = _to_s16(data[0],  data[1])
        self.AC2 = _to_s16(data[2],  data[3])
        self.AC3 = _to_s16(data[4],  data[5])
        self.AC4 = _to_u16(data[6],  data[7])
        self.AC5 = _to_u16(data[8],  data[9])
        self.AC6 = _to_u16(data[10], data[11])
        self.B1  = _to_s16(data[12], data[13])
        self.B2  = _to_s16(data[14], data[15])
        self.MB  = _to_s16(data[16], data[17])
        self.MC  = _to_s16(data[18], data[19])
        self.MD  = _to_s16(data[20], data[21])

    def _read_raw_temp(self):
        self.bus.write_byte_data(self.addr, REG_CONTROL, CMD_TEMP)
        time.sleep(CONV_WAIT_S[0])
        msb = self.bus.read_byte_data(self.addr, REG_RESULT)
        lsb = self.bus.read_byte_data(self.addr, REG_RESULT + 1)
        return (msb << 8) | lsb

    def _read_raw_pressure(self):
        cmd = CMD_PRESSURE + (self.oss << 6)
        self.bus.write_byte_data(self.addr, REG_CONTROL, cmd)
        time.sleep(CONV_WAIT_S[self.oss])
        msb = self.bus.read_byte_data(self.addr, REG_RESULT)
        lsb = self.bus.read_byte_data(self.addr, REG_RESULT + 1)
        xlsb = self.bus.read_byte_data(self.addr, REG_RESULT + 2)
        up = ((msb << 16) | (lsb << 8) | xlsb) >> (8 - self.oss)
        return up

    def _read_temp_and_pressure(self):
        ut = self._read_raw_temp()

        # Temperature compensation
        x1 = ((ut - self.AC6) * self.AC5) >> 15
        x2 = (self.MC << 11) // (x1 + self.MD)
        b5 = x1 + x2
        temp_c = ((b5 + 8) >> 4) / 10.0

        # Pressure compensation
        up = self._read_raw_pressure()
        b6 = b5 - 4000
        x1 = (self.B2 * ((b6 * b6) >> 12)) >> 11
        x2 = (self.AC2 * b6) >> 11
        x3 = x1 + x2
        b3 = (((self.AC1 * 4 + x3) << self.oss) + 2) >> 2
        x1 = (self.AC3 * b6) >> 13
        x2 = (self.B1 * ((b6 * b6) >> 12)) >> 16
        x3 = (x1 + x2 + 2) >> 2
        b4 = (self.AC4 * (x3 + 32768)) >> 15
        b7 = (up - b3) * (50000 >> self.oss)

        if b7 < 0x80000000:
            p = (b7 * 2) // b4
        else:
            p = (b7 // b4) * 2

        x1 = (p >> 8) * (p >> 8)
        x1 = (x1 * 3038) >> 16
        x2 = (-7357 * p) >> 16
        p = p + ((x1 + x2 + 3791) >> 4)

        return temp_c, int(p)

    def read_altitude(self, p0=101325.0):
        """Return altitude in meters, using given sea-level pressure (Pa)."""
        _, p = self._read_temp_and_pressure()
        return 44330.0 * (1.0 - (p / p0) ** (1.0 / 5.255))


def main():
    print("Starting BMP180 altitude readout...")
    with SMBus(1) as bus:
        sensor = BMP180(bus)
        sea_level_pressure = 101325.0  # Pa; change for local calibration
        while True:
            try:
                alt = sensor.read_altitude(sea_level_pressure)
                print(f"Altitude: {alt:8.2f} m")
                time.sleep(.05)
            except KeyboardInterrupt:
                print("\nExiting.")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1.0)


if __name__ == "__main__":
    main()
