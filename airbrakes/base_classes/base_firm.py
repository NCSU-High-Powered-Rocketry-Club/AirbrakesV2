from abc import ABC, abstractmethod

from firm_client import FIRMData


class BaseFIRM(ABC):
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
    def get_data_packets(self) -> list[FIRMData]:
        """
        Returns all available FIRM data packets from the queued FIRM packets.

        :return: A list containing the latest FIRM data packets from the FIRM packet queue.
        """
