import time

from raspberry_py.gpio import cleanup
from raspberry_py.gpio.sensors import MjpgStreamer
from raspberry_py.utils import get_local_ip_address


def main():
    """
    This example uses the mjpg-streamer component.
    """

    camera = MjpgStreamer(
        device='/dev/video0',
        width=640,
        height=480,
        fps=30,
        quality=100,
        port=8082
    )
    camera.turn_on()

    try:
        while True:
            print(f'Streaming...visit http://{get_local_ip_address()}:{camera.port} to view stream.')
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass

    camera.turn_off()
    cleanup()


if __name__ == '__main__':
    main()
