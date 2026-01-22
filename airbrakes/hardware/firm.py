from firm_client import FIRMClient, FIRMData

from airbrakes.base_classes.base_firm import BaseFIRM


class FIRM(BaseFIRM):
    __slots__ = ("firm_client",)

    def __init__(self):
        self.firm_client = FIRMClient(PORT, BAUD_RATE, SERIAL_TIMEOUT_SECONDS)

    def start(self) -> None:
        """
        Starts the FIRM client for fetching data packets.
        """
        self.firm_client.start()

    def stop(self) -> None:
        """
        Stops the FIRM client for fetching data packets.
        """
        self.firm_client.stop()

    def get_data_packets(self) -> list[FIRMData]:
        """
        Returns all available FIRM data packets from the queued FIRM packets.

        :return: A list containing the latest FIRM data packets from the FIRM packet queue.
        """
        return self.firm_client.get_data_packets()
