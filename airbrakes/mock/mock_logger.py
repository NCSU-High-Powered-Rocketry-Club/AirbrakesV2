"""Mock Logger class for testing purposes. Currently only used to delete the log file."""

from pathlib import Path

from airbrakes.data_handling.logger import Logger


class MockLogger(Logger):
    """This class has the same functionality as the Logger class, but simply removes the log file it
    generates after the logger has stopped.
    """

    __slots__ = ("delete_log_file",)

    def __init__(self, log_file_path: Path, delete_log_file: bool = True):
        super().__init__(log_file_path)
        self.delete_log_file = delete_log_file
        self._log_process.name = "Mock Logger Process"

    def stop(self):
        """Stops the logger and deletes the log file if the delete_log_file attribute is True."""
        super().stop()
        if self.delete_log_file:
            self.log_path.unlink()
