import time
from threading import RLock
from typing import Optional

from serial import Serial


class LockingSerial:
    """
    Serial connection with a lock object for use across multiple objects.
    """

    def __init__(
            self,
            connection: Serial,
            throughput_step_size: float,
            manual_buffer: bool
    ):
        """
        Initialize the serial connection.

        :param connection: Serial connection.
        :param throughput_step_size: Step size in (0.0, 1.0] used to estimate throughput. Smaller step sizes create less
        variance but more lag in the estimate, whereas larger step sizes create more variance but less lag.
        :param manual_buffer: Whether to manually buffer all bytes. Any written bytes will be held back until the
        current object's `flush_manually` function is called, at which point all bytes will be written to the serial
        connection and flushed. If False, then Python's standard buffering in the Serial class will be used.
        """

        self.connection = connection
        self.throughput_step_size = throughput_step_size
        self.manual_buffer = manual_buffer

        self.lock = RLock()
        self.throughput_time_epoch_seconds: Optional[float] = None
        self.bytes_read_per_second = 0.0
        self.bytes_written_per_second = 0.0
        self.buffer = []

    def write_then_read(
            self,
            data: bytes,
            flush: bool,
            read_length: int,
            readline: bool
    ) -> bytes:
        """
        Write bytes and then read response. Note that, when buffering manually, flush has no effect, and it is not
        permitted to read any data.

        :param data: Bytes to write.
        :param flush: Whether to flush the output stream after writing the data.
        :param read_length: Number of bytes to read (use -1 when `readline` is True to read up to newline). Must be >=
        0 if `readline` is False.
        :param readline: Whether to read a line of string content.
        :return: Bytes that were read.
        """

        with self.lock:

            if self.manual_buffer:

                if read_length > 0 or readline:
                    raise ValueError('Cannot read data with write_then_read when buffering manually.')

                self.buffer.extend(data)
                bytes_read = bytes()

            else:

                self.connection.write(data)

                if flush:
                    self.connection.flush()

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

                self.update_throughput(
                    len(data) if len(data) > 0 else None,
                    num_bytes_read if num_bytes_read > 0 else None
                )

            return bytes_read

    def flush_manually(
            self
    ):
        """
        Flush the manual buffer.
        """

        with self.lock:

            if not self.manual_buffer:
                raise ValueError('Expected to be in manual buffer mode.')

            self.connection.write(bytes(self.buffer))
            self.connection.flush()
            self.update_throughput(len(self.buffer) if len(self.buffer) > 0 else None, None)
            self.buffer.clear()

    def update_throughput(
            self,
            num_bytes_written: Optional[int],
            num_bytes_read: Optional[int]
    ):
        """
        Update throughput estimates.

        :param num_bytes_written: Number of bytes written.
        :param num_bytes_read: Number of bytes read.
        """

        current_time_epoch_seconds = time.time()

        if self.throughput_time_epoch_seconds is not None:
            elapsed_seconds = current_time_epoch_seconds - self.throughput_time_epoch_seconds

            if num_bytes_written is not None:
                self.bytes_written_per_second = (
                    (1.0 - self.throughput_step_size) * self.bytes_written_per_second +
                    self.throughput_step_size * (num_bytes_written / elapsed_seconds)
                )

            if num_bytes_read is not None:
                self.bytes_read_per_second = (
                    (1.0 - self.throughput_step_size) * self.bytes_read_per_second +
                    self.throughput_step_size * (num_bytes_read / elapsed_seconds)
                )

        self.throughput_time_epoch_seconds = current_time_epoch_seconds
