"""Base class for FIRM."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from firm_client import FIRMDataPacket


class BaseFIRM(ABC):
    """
    A base class for FIRM devices, providing an interface for fetching data
    packets.
    """

    __slots__ = ()

    @property
    @abstractmethod
    def requested_to_run(self) -> bool:
        """
        Returns whether the thread fetching data from FIRM has been requested to run.

        :return: True if the thread is requested to run, False otherwise.
        """

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """
        Returns whether FIRM is running.

        :return: True if the thread is running, False otherwise.
        """

    @abstractmethod
    def start(self) -> None:
        """Starts the FIRM client for fetching data packets."""

    @abstractmethod
    def stop(self) -> None:
        """Stops the FIRM client for fetching data packets."""

    @abstractmethod
    def get_data_packets(self, block: bool = True) -> list[FIRMDataPacket]:
        """
        Returns all available FIRM data packets from the queued FIRM
        packets.

        :param block: If True, blocks until at least one data packet is available.

        :return: A list containing the latest FIRM data packets from the
            FIRM packet queue.
        """
