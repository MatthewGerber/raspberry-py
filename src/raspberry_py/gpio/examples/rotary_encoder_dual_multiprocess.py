import time
from multiprocessing import set_start_method

from raspberry_py.gpio import CkPin
from raspberry_py.gpio.sensors import MultiprocessRotaryEncoder, RotaryEncoder


def main():
    """
    Example of using dual multiprocess encoders to accurately measure speed and direction. This obtains the accuracy
    benefits of biphase detection while maintaining the speed (lack of callback loss) of uniphase detection. This comes
    at the expense of using an additional process (CPU core).
    """

    speed_encoder = MultiprocessRotaryEncoder(
        phase_a_pin=CkPin.GPIO17,
        phase_b_pin=CkPin.GPIO27,
        phase_changes_per_rotation=1200,
        phase_change_mode=RotaryEncoder.PhaseChangeMode.BIPHASE,
        degrees_per_second_step_size=1.0
    )
    speed_encoder.wait_for_startup()

    # direction_encoder = MultiprocessRotaryEncoder(
    #     phase_a_pin=CkPin.GPIO17,
    #     phase_b_pin=CkPin.GPIO27,
    #     phase_changes_per_rotation=1200,
    #     phase_change_mode=RotaryEncoder.PhaseChangeMode.BIPHASE,
    #     degrees_per_second_step_size=1.0
    # )
    # direction_encoder.wait_for_startup()

    try:
        start_epoch = time.time()
        while time.time() - start_epoch < 300.0:
            time.sleep(1.0 / 50.0)
            speed_encoder.update_state()
            speed_state: MultiprocessRotaryEncoder.State = speed_encoder.state
            print(f'Degrees:  {speed_state.degrees}; RPM:  {60.0 * speed_state.degrees_per_second / 360.0:.1f}')

            # direction_encoder.update_state()
            # direction_state: MultiprocessRotaryEncoder.State = direction_encoder.state
            # speed_encoder.clockwise.value = direction_state.clockwise

        # direction_encoder.wait_for_termination()
        speed_encoder.wait_for_termination()

    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    set_start_method('spawn')
    main()
