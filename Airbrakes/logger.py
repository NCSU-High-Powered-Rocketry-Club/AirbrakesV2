import logging
import os
import multiprocessing
import queue
from Airbrakes.imu import IMUDataPacket


class Logger:
    def __init__(self, csv_headers: list[str]):
        self.csv_headers = csv_headers

        self.log_path = os.path.join("logs", "log1.csv")

        # Creates a new CSV file with the specified headers
        while True:
            if not os.path.exists(self.log_path):
                with open(self.log_path, "w", newline="") as file_writer:
                    file_writer.write(",".join(csv_headers) + "\n")
                    break
            self.log_path = self.log_path[:-5] + str(int(self.log_path[-5]) + 1) + ".csv"

        self.log_queue = multiprocessing.Queue()
        self.running = multiprocessing.Value('b', True)  # Makes a boolean value that is shared between processes

        # Start the logging process
        self.log_process = multiprocessing.Process(target=self._logging_loop)
        self.log_process.start()

    def _logging_loop(self):
        """
        The loop that saves data to the logs. It runs in parallel with the main loop.
        """
        # Set up the logger in the new process
        logger = logging.getLogger("logger")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.log_path, mode="a")  # Append to the file
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

        while self.running.value:
            # Get a message from the queue (this will block until a message is available)
            # Because there's no timeout, it will wait indefinitely until it gets a message -- this is fine in practice,
            # but if for some reason the queue is empty, it will block forever and stop() won't work
            message = self.log_queue.get()
            logger.info(message)

    def log(self, state: str, extension: float, imu_data: IMUDataPacket):
        """
        Logs the current state, extension, and IMU data to the CSV file.
        :param state: the current state of the airbrakes state machine
        :param extension: the current extension of the airbrakes
        :param imu_data: the current IMU data
        """
        # Formats the log message as a CSV line
        message = f"{state},{extension},{','.join([str(value) for value in imu_data.__dict__.values()])}"
        # Put the message in the queue
        self.log_queue.put(message)

    def stop(self):
        """
        Stops the logging process. It will finish logging the current message and then stop.
        """
        self.running.value = False
        # Waits for the process to finish before stopping it
        self.log_process.join()