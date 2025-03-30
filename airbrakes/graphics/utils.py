"""Utility functions for the graphics module."""

import bisect
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Self

from textual.widget import Widget


class InformationStore:
    """Class to store the information to be displayed in the graphs. A set amount of time's
    worth of data is stored as a rolling buffer. This class is independent of the TUI, because
    it is meant to be extensible and reusable, for example for use in scripts, to show other IMU
    data.
    """

    __slots__ = ("data", "time_to_store_for")

    def __init__(self, time_to_store_for: float | None) -> None:
        """Initializes the InformationStore.

        :param time_to_store_for: The amount of time to store data for. If None, all data is stored.
        """
        self.time_to_store_for = time_to_store_for
        self.data: dict[str, list[float]] = {}

    def initalize_new_data(self, data_name: str) -> None:
        """Initializes a new data set to store in the buffer.

        :param data_name: The name of the data to store.
        """
        self.data[data_name] = []

    def add_data_point(self, data_name: str, data: float) -> None:
        """Adds data to the buffer.

        :param data_name: The name of the data to store.
        :param data: The data to store.
        """
        self.data[data_name].append(data)

    def get_data(self, data_name: str) -> list[float]:
        """Returns the data stored in the buffer.

        :param data_name: The name of the data to return.
        """
        return self.data[data_name]

    @contextmanager
    def resize_data(self) -> Generator[Self]:
        """Trims the data if the time difference between the first and last data points is greater
        than the time to store for.

        Use as:
        ```
        with information_store.resize_data() as store:
            store.add_data_point("data_name", data)
        ```
        """
        yield self
        # The numpy approach is slower by about 30%
        last_time = self.data["time"][-1]
        min_time = last_time - self.time_to_store_for
        min_time_index = bisect.bisect_left(self.data["time"], min_time)

        for data_name in self.data:
            self.data[data_name] = self.data[data_name][min_time_index:]


def get_date_from_iso_string(input_string: str) -> str:
    """Gets the date from an ISO string and formats it to 'ddth Month, YYYY'."""
    datetime_obj = datetime.fromisoformat(input_string)
    return datetime_obj.strftime("%d{} %B, %Y").format(
        "th"
        if 11 <= datetime_obj.day <= 13
        else {1: "st", 2: "nd", 3: "rd"}.get(datetime_obj.day % 10, "th")
    )


def get_time_from_iso_string(input_string: str) -> str:
    """Gets the time from an ISO string and formats it to 'HH:MM AM/PM'."""
    datetime_obj = datetime.fromisoformat(input_string)
    return datetime_obj.strftime("%I:%M %p").lstrip("0").replace("AM", "am").replace("PM", "pm")


def format_seconds_to_mins_and_secs(seconds: int) -> str:
    """Converts seconds to a string in the format 'm:ss'."""
    return f"{seconds // 60:.0f}:{seconds % 60:02.0f}"


def set_only_class(obj: Widget, class_name: str) -> None:
    """Sets the only class of the object to the given class name, removes all others."""
    obj.remove_class(*obj.classes)
    obj.set_class(True, class_name)
