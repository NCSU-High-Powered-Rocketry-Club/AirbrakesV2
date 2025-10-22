#!/usr/bin/env python3
"""
Simple script to read current from the Gravity I2C Digital Wattmeter (SEN0291) using INA219.
"""

import time
import sys

# If using the pi-ina219 library:
from ina219 import INA219, DeviceRangeError

# Configuration parameters – adjust as needed:
SHUNT_OHMS = 0.01   # The board uses a 10 mΩ (0.01 Ω) shunt resistor according to spec. :contentReference[oaicite:6]{index=6}
MAX_EXPECTED_AMPS = 8.0   # Up to ±8A per spec. :contentReference[oaicite:7]{index=7}
I2C_ADDRESS = 0x45        # Example address (check your board’s DIP switch)
I2C_BUS_NUMBER = 1        # On many Raspberry Pi boards I2C bus is 1

def main():
    try:
        ina = INA219(
            shunt_ohms=SHUNT_OHMS,
            max_expected_amps=MAX_EXPECTED_AMPS,
            address=I2C_ADDRESS,
            busnum=I2C_BUS_NUMBER
        )
        ina.configure()
    except Exception as e:
        print("Failed to initialize INA219:", e)
        sys.exit(1)

    print("Starting measurements. Press Ctrl-C to quit.")
    try:
        while True:
            bus_voltage = ina.voltage()            # in volts
            current_mA = ina.current()             # in mA
            power_mW = ina.power()                 # in mW
            shunt_voltage_mV = ina.shunt_voltage() # in mV

            print(f"Bus Voltage:     {bus_voltage:.3f} V")
            print(f"Shunt Voltage:   {shunt_voltage_mV:.3f} mV")
            print(f"Current:         {current_mA:.3f} mA")
            print(f"Power:           {power_mW:.3f} mW")
            print("-------------------------------------")

            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nExiting.")
    except DeviceRangeError as e:
        print("Device Range Error:", e)
    except Exception as e:
        print("Unexpected error:", e)

if __name__ == '__main__':
    main()
