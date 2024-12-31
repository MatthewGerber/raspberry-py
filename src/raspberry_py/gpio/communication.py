from threading import Lock

from serial import Serial


class LockingSerial:
    """
    Serial connection with a lock object for use across multiple objects.
    """

    def __init__(
            self,
            connection: Serial
    ):
        """
        Initialize the serial connection.

        :param connection: Serial connection.
        """

        self.connection = connection

        self.lock = Lock()

    def write_then_read(
            self,
            data: bytes,
            read_length: int
    ) -> bytes:
        """
        Write bytes and then read response.

        :param data: Bytes to write.
        :param read_length: Number of bytes to read.
        :return: Bytes that were read.
        """

        with self.lock:

            self.connection.write(data)

            if read_length == 0:
                bytes_read = bytes()
            else:
                bytes_read = self.connection.read(read_length)

            num_bytes_read = len(bytes_read)
            if num_bytes_read != read_length:
                raise ValueError(f'Expected to read {read_length} byte(s) but read {num_bytes_read}.')

            return bytes_read
