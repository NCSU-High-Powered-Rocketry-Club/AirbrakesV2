"""
This module contains the FIRM class, which is responsible for fetching data
packets from FIRM.
"""

from typing import TYPE_CHECKING

from firm_client import FIRMClient, FIRMDataPacket

from airbrakes.base_classes.base_firm import BaseFIRM
from airbrakes.constants import FIRM_BAUD_RATE, FIRM_PORT, FIRM_SERIAL_TIMEOUT_SECONDS

if TYPE_CHECKING:
    from pathlib import Path


class FIRM(BaseFIRM):
    """
    A custom class that represents the FIRM device, which is responsible for
    fetching data packets from FIRM.
    """

    __slots__ = ("_log_file_path", "firm_client", "is_pretend")

    def __init__(self, is_pretend=False, log_file_path: Path | None = None):
        super().__init__()
        self.is_pretend = is_pretend
        self._log_file_path = log_file_path
        self.firm_client = FIRMClient(FIRM_PORT, FIRM_BAUD_RATE, FIRM_SERIAL_TIMEOUT_SECONDS)

    @property
    def is_running(self) -> bool:
        return self.firm_client.is_running()

    @property
    def requested_to_run(self) -> bool:
        """Returns whether the thread fetching data from FIRM has been requested to run."""
        return self.is_running

    def start(self) -> None:
        """Starts the FIRM client for fetching data packets."""
        self.firm_client.start()

        if self.is_pretend:
            self.firm_client.start_mock_log_stream(str(self._log_file_path))
        super().start()

    def stop(self) -> None:
        """Stops the FIRM client for fetching data packets."""
        self.firm_client.stop()
        super().stop()

    def get_data_packets(self, block: bool = True) -> list[FIRMDataPacket]:
        """
        Returns all available FIRM data packets from the queued FIRM
        packets.

        :return: A list containing the latest FIRM data packets from the
            FIRM packet queue.
        """
        # Throws out any packets collected before FIRM responds that it's in mock mode
        if self.is_pretend and not self.firm_client.is_mock_log_streaming():
            return []

        # Otherwise we just return the data packets like normal
        return self.firm_client.get_data_packets(block=block)
