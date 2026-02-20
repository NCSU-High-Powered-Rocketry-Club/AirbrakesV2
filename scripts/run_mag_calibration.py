import firm_client

from airbrakes.constants import FIRM_PORT

import threading
import time

client = firm_client.FIRMClient(FIRM_PORT)
client.start()


def _countdown(seconds: int, label: str, stop_event: threading.Event | None = None) -> None:
    """Print a simple 1 Hz countdown.

    If stop_event is set, exits early.
    """
    for remaining in range(int(seconds), 0, -1):
        if stop_event is not None and stop_event.is_set():
            return
        print(f"{label} {remaining}s", flush=True)
        time.sleep(1)


def print_mag_calibration(label: str) -> None:
    cal = client.get_calibration(timeout_seconds=2.0)
    if cal is None:
        print(f"{label}: <no calibration response>")
        return

    print(f"{label}:")
    print(f"  mag offsets: {cal.magnetometer_offsets}")
    print(f"  mag matrix:  {cal.magnetometer_scale_matrix}")


print_mag_calibration("Before calibration")

try:
    _countdown(10, "Starting calibration in")

    print("Please rotate the device in all directions...")

    # This line will block for 30 seconds
    _stop_countdown = threading.Event()
    _t = threading.Thread(
        target=_countdown,
        kwargs={
            "seconds": 30,
            "label": "Calibrating (keep rotating) —",
            "stop_event": _stop_countdown,
        },
        daemon=True,
    )
    _t.start()

    try:
        result = client.run_and_apply_magnetometer_calibration(
            collection_duration_seconds=30.0, apply_timeout_seconds=1.0
        )
    finally:
        _stop_countdown.set()
        _t.join(timeout=2.0)

    if result is True:
        print("Calibration Success! Applied to device.")
    elif result is False:
        print("Calibration calculated, but device rejected the update.")
    elif result is None:
        print("Calibration Failed: Not enough data points.")
    else:
        print("Error occurred.")

    print_mag_calibration("After calibration")

except KeyboardInterrupt:
    print("Cancelled by user.")
finally:
    client.stop()
