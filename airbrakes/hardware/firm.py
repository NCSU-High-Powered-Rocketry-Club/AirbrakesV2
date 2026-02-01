from firm_client import FIRMClient, FIRMDataPacket

from airbrakes.base_classes.base_firm import BaseFIRM
from airbrakes.constants import FIRM_PORT, FIRM_BAUD_RATE, FIRM_SERIAL_TIMEOUT_SECONDS


class FIRM(BaseFIRM):
    __slots__ = ("firm_client",)

    def __init__(self):
        super().__init__()
        self.firm_client = FIRMClient(FIRM_PORT, FIRM_BAUD_RATE, FIRM_SERIAL_TIMEOUT_SECONDS)

    def start(self) -> None:
        """
        Starts the FIRM client for fetching data packets.
        """
        self.firm_client.start()
        super().start()

    def stop(self) -> None:
        """
        Stops the FIRM client for fetching data packets.
        """
        self.firm_client.stop()
        super().stop()

    def get_data_packets(self) -> list[FIRMDataPacket]:
        """
        Returns all available FIRM data packets from the queued FIRM packets.

        :return: A list containing the latest FIRM data packets from the FIRM packet queue.
        """
        return self.firm_client.get_data_packets()
