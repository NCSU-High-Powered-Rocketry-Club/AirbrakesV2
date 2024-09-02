import logging
import os
import multiprocessing
from Airbrakes.imu import IMUDataPacket

class Logger:
    def __init__(self, csv_headers: list[str]):
        self.log_path = os.path.join("logs", "log1.csv")
        self.csv_headers = csv_headers

        # Create the CSV file with headers if it doesn't exist
        while True:
            if not os.path.exists(self.log_path):
                with open(self.log_path, "w", newline="") as file_writer:
                    file_writer.write(",".join(csv_headers) + "\n")
                    break
            self.log_path = self.log_path[:-5] + str(int(self.log_path[-5]) + 1) + ".csv"

        self.log_queue = multiprocessing.Queue()
        self.running = multiprocessing.Value('b', True)  # Makes a boolean value that is shared between processes

        # Start the logging process
        self.log_process = multiprocessing.Process(target=self._logger_process, args=(self.running,))
        self.log_process.start()

    def _logger_process(self, running):
        # Set up the logger in the new process
        logger = logging.getLogger("logger_process")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(self.log_path)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

        while running.value:
            try:
                # Get a message from the queue (wait for it)
                message = self.log_queue.get(timeout=0.1)  # Use a timeout to check running status
                logger.info(message)
            except:
                continue  # No message in the queue, continue checking

    def log(self, state: str, extension: float, imu_data: IMUDataPacket):
        # Format the log message as a CSV line
        message = f"{state},{extension},{','.join([str(value) for value in imu_data.__dict__.values()])}"
        # Put the message in the queue
        self.log_queue.put(message)

    def stop(self):
        # Set running to False to stop the logging process
        self.running.value = False
        self.log_process.join()
