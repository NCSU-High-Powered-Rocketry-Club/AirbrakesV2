from firm_client import FIRMClient
import csv


def main() -> None:
    port = "/dev/ttyACM0"   # Change if needed
    baud_rate = 2_000_000

    with FIRMClient(port, baud_rate, timeout=0.2) as client, \
         open("mag_data.csv", "w", newline="") as f:

        writer = csv.writer(f)
        writer.writerow(["timestamp_s", "mag_x_uT", "mag_y_uT", "mag_z_uT"])

        client.get_data_packets(block=True)  # Clear initial packets

        while client.is_running():
            packets = client.get_data_packets(block=True)

            for packet in packets:
                writer.writerow([
                    packet.timestamp_seconds,
                    packet.magnetic_field_x_microteslas,
                    packet.magnetic_field_y_microteslas,
                    packet.magnetic_field_z_microteslas,
                ])

            f.flush()  # Ensures data is written immediately


if __name__ == "__main__":
    main()