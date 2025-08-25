import time
from threading import Lock
from typing import Optional

from serial import Serial


class LockingSerial:
    """
    Serial connection with a lock object for use across multiple objects.
    """

    def __init__(
            self,
            connection: Serial,
            throughput_step_size: float
    ):
        """
        Initialize the serial connection.

        :param connection: Serial connection.
        :param throughput_step_size: Step size in (0.0, 1.0] used to estimate throughput. Smaller step sizes create less
        variance but more lag in the estimate, whereas larger step sizes create more variance but less lag.
        """

        self.connection = connection
        self.throughput_step_size = throughput_step_size

        self.lock = Lock()
        self.throughput_time_epoch_seconds: Optional[float] = None
        self.bytes_read_per_second = 0.0
        self.bytes_written_per_second = 0.0

    def write_then_read(
            self,
            data: bytes,
            read_length: int,
            readline: bool
    ) -> bytes:
        """
        Write bytes and then read response.

        :param data: Bytes to write.
        :param read_length: Number of bytes to read (use -1 when `readline` is True to read up to newline). Must be >=
        0 if `readline` is False.
        :param readline: Whether to read a line of string content.
        :return: Bytes that were read.
        """

        with self.lock:

            self.connection.write(data)

            if read_length == 0:
                bytes_read = bytes()
            else:
                if readline:
                    bytes_read = self.connection.readline(read_length)
                else:
                    if read_length < 0:
                        raise ValueError(f'Invalid read length:  {read_length}')
                    else:
                        bytes_read = self.connection.read(read_length)

            num_bytes_read = len(bytes_read)
            if read_length != -1 and num_bytes_read != read_length:
                raise ValueError(f'Expected to read {read_length} byte(s) but read {num_bytes_read}.')

            # update throughput estimates
            current_time_epoch_seconds = time.time()
            if self.throughput_time_epoch_seconds is not None:
                elapsed_seconds = current_time_epoch_seconds - self.throughput_time_epoch_seconds
                self.bytes_written_per_second = (
                    (1.0 - self.throughput_step_size) * self.bytes_written_per_second +
                    self.throughput_step_size * (len(data) / elapsed_seconds)
                )
                self.bytes_read_per_second = (
                    (1.0 - self.throughput_step_size) * self.bytes_read_per_second +
                    self.throughput_step_size * (num_bytes_read / elapsed_seconds)
                )
            self.throughput_time_epoch_seconds = current_time_epoch_seconds

            return bytes_read
