import gpiod
import time
from gpiod.line import Direction, Value


CHIP_NAME = "/dev/gpiochip0"
PIN_NO = 26

def main():
    request = gpiod.request_lines(
        path=CHIP_NAME,
        consumer="gpio26-manual-toggle",
        config={
            PIN_NO: gpiod.LineSettings(direction=Direction.OUTPUT)
        },
    )
    
    try:
        # 2. Drive it HIGH
        request.set_value(PIN_NO, Value.ACTIVE)
        print("GPIO26 is HIGH")
        time.sleep(1.0)
        
        # 3. Drive it LOW
        request.set_value(PIN_NO, Value.INACTIVE)
        print("GPIO26 is LOW")
        time.sleep(1.0)

    finally:
        # 4. Manually release the line so other programs can use it
        request.release()

main()
