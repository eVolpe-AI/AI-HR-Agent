import time
from datetime import datetime
import os
from dotenv import load_dotenv

class TimeLogger:

    default_log_file = '/tmp/execution_times.txt'
    start_time_ns = 0

    def end_log(self, message = 'miejsce wywolania'):
        load_dotenv()
        log_time = os.getenv("LOG_TIME", 0)
        log_file = os.getenv("LOG_FILE", self.default_log_file)
        if log_time == 0:
            return
        end_time_ns = time.time_ns()
        execution_time_ms = (end_time_ns - self.start_time_ns) / 1e6
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, 'a') as file:
            file.write(f"{timestamp} - Czas wykonania {message}: {execution_time_ms:.4f} milliseconds\n")


    def start_log(self):
        self.start_time_ns = time.time_ns()
