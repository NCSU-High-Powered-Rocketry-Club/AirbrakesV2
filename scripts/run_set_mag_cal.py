import firm_client

from airbrakes.constants import FIRM_PORT

client = firm_client.FIRMClient(FIRM_PORT)
client.start()


def print_mag_calibration(label: str) -> None:
    cal = client.get_calibration(timeout_seconds=2.0)
    if cal is None:
        print(f"{label}: <no calibration response>")
        return

    print(f"{label}:")
    print(f"  mag offsets: {cal.magnetometer_offsets}")
    print(f"  mag matrix:  {cal.magnetometer_scale_matrix}")


print_mag_calibration("Before calibration")


MAG_OFFSETS = (0.0, 0.0, 0.0)

MAG_IDENTITY_SCALE = (
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
)
ok = client.set_magnetometer_calibration(
    MAG_OFFSETS,
    MAG_IDENTITY_SCALE,
)

client.stop()
