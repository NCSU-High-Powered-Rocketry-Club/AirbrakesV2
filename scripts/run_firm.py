from firm_client import FIRMClient


def main() -> None:
    port = "COM12"  # Update as needed (e.g., "COM8" or "/dev/ttyACM0")
    baud_rate = 2_000_000

    initial_dt = 0

    with FIRMClient(port, baud_rate, timeout=.2) as client:
        client.get_data_packets(block=True)  # Clear initial packets
        while client.is_running():
            packets = client.get_data_packets(block=True)
            print(f"Received {len(packets)} packets")
            for packet in packets:
                print(f"""
                    --- FIRM Packet ({packet.timestamp_seconds:.4f}s) ---
                    Env:      {packet.temperature_celsius:.2f}°C | {packet.pressure_pascals:.2f} Pa

                    Raw Accel (G):      x={packet.raw_acceleration_x_gs: >8.4f}, y={packet.raw_acceleration_y_gs: >8.4f}, z={packet.raw_acceleration_z_gs: >8.4f}
                    Raw Gyro (d/s):     x={packet.raw_angular_rate_x_deg_per_s: >8.4f}, y={packet.raw_angular_rate_y_deg_per_s: >8.4f}, z={packet.raw_angular_rate_z_deg_per_s: >8.4f}
                    Mag Field (uT):     x={packet.magnetic_field_x_microteslas: >8.4f}, y={packet.magnetic_field_y_microteslas: >8.4f}, z={packet.magnetic_field_z_microteslas: >8.4f}
                    Est Pos (m):        x={packet.est_position_x_meters: >8.4f}, y={packet.est_position_y_meters: >8.4f}, z={packet.est_position_z_meters: >8.4f}
                    Est Vel (m/s):      x={packet.est_velocity_x_meters_per_s: >8.4f}, y={packet.est_velocity_y_meters_per_s: >8.4f}, z={packet.est_velocity_z_meters_per_s: >8.4f}
                    Est Accel (G):      x={packet.est_acceleration_x_gs: >8.4f}, y={packet.est_acceleration_y_gs: >8.4f}, z={packet.est_acceleration_z_gs: >8.4f}
                    Est Rate (rad/s):   x={packet.est_angular_rate_x_rad_per_s: >8.4f}, y={packet.est_angular_rate_y_rad_per_s: >8.4f}, z={packet.est_angular_rate_z_rad_per_s: >8.4f}
                    Est Quat:           w={packet.est_quaternion_w: >6.3f}, x={packet.est_quaternion_x: >6.3f}, y={packet.est_quaternion_y: >6.3f}, z={packet.est_quaternion_z: >6.3f}
                    -------------------------------------------
                    """)
            print(
                f"Time since last packet: "
                f"{(packets[-1].timestamp_seconds - initial_dt) * 1e3:.9f} ms"
            )
            initial_dt = packets[-1].timestamp_seconds


main()
