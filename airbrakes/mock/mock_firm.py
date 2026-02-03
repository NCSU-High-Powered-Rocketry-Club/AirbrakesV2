from typing import TYPE_CHECKING

from airbrakes.base_classes.base_firm import BaseFIRM

if TYPE_CHECKING:
    from firm_client import FIRMDataPacket


# TODO: implement this later
class MockFIRM(BaseFIRM):
    def __init__(self):
        super().__init__()

    def start(self) -> None:
        """
        Starts the FIRM client for fetching data packets.
        """
        super().start()

    def stop(self) -> None:
        """
        Stops the FIRM client for fetching data packets.
        """
        super().stop()

    def get_data_packets(self) -> list[FIRMDataPacket]:
        """
        Returns all available FIRM data packets from the queued FIRM packets.

        :return: A list containing the latest FIRM data packets from the FIRM packet queue.
        """
        return []
