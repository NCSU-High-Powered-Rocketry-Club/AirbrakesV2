from abc import ABC, abstractmethod

from firm_client import FIRMDataPacket


class BaseFIRM(ABC):
    __slots__ = ("_running",)

    def __init__(self):
        self._running = False

    @property
    def is_running(self) -> bool:
        """
        Returns whether FIRM is running.

        :return: True if the thread is running, False otherwise.
        """
        return self._running

    @abstractmethod
    def start(self) -> None:
        """
        Starts the FIRM client for fetching data packets.
        """
        self._running = True

    @abstractmethod
    def stop(self) -> None:
        """
        Stops the FIRM client for fetching data packets.
        """
        self._running = False

    @abstractmethod
    def get_data_packets(self) -> list[FIRMDataPacket]:
        """
        Returns all available FIRM data packets from the queued FIRM packets.

        :return: A list containing the latest FIRM data packets from the FIRM packet queue.
        """
