from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from firm_client import FIRMDataPacket


class BaseFIRM(ABC):
    @property
    @abstractmethod
    def is_running(self) -> bool:
        """
        Returns whether FIRM is running.

        :return: True if the thread is running, False otherwise.
        """

    @abstractmethod
    def start(self) -> None:
        """
        Starts the FIRM client for fetching data packets.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Stops the FIRM client for fetching data packets.
        """

    @abstractmethod
    def get_data_packets(self) -> list[FIRMDataPacket]:
        """
        Returns all available FIRM data packets from the queued FIRM packets.

        :return: A list containing the latest FIRM data packets from the FIRM packet queue.
        """
