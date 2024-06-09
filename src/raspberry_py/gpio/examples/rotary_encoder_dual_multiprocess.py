import time

from raspberry_py.gpio import CkPin, setup, cleanup
from raspberry_py.gpio.sensors import MultiprocessRotaryEncoder, DualMultiprocessRotaryEncoder


def main():
    """
    Example of using a dual multiprocess rotary encoder.
    """

    setup()

    encoder = DualMultiprocessRotaryEncoder(
        CkPin.GPIO5,
        CkPin.GPIO17,
        CkPin.GPIO27,
        1200,
        1.0
    )
    encoder.wait_for_startup()

    try:
        while True:
            time.sleep(1.0/10.0)
            encoder.update_state()
            state: MultiprocessRotaryEncoder.State = encoder.state
            print(
                f'Degrees:  {state.degrees}; RPM:  {60.0 * state.degrees_per_second / 360.0:.1f} '
                f'(clockwise={state.clockwise})'
            )
    except KeyboardInterrupt:
        encoder.wait_for_termination()
        time.sleep(1.0)

    cleanup()


if __name__ == '__main__':
    main()
