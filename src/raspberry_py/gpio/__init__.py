import logging
import time
import uuid
from abc import ABC, abstractmethod
from copy import deepcopy
from enum import IntEnum
from threading import Thread, RLock
from typing import List, Callable, Optional, Dict

import RPi.GPIO as gpio


def setup():
    """
    Set up the GPIO interface.
    """

    gpio.setwarnings(False)
    gpio.setmode(gpio.BOARD)


def cleanup():
    """
    Clean up the GPIO interface.
    """

    gpio.cleanup()


class Pin(IntEnum):
    """
    GPIO pins and their board pin numbers, corresponding to the pinout provided in the Raspberry Pi documentation:

    https://github.com/raspberrypi/documentation/blob/develop/documentation/asciidoc/computers/os/using-gpio.adoc#gpio-and-the-40-pin-header

    Other Raspberry Pi hardware manufacturers and distributors use varying names for the pins, both in their
    documentation and printed on their hardware. See the classes following this one for alternative name/pin mappings.
    """

    GPIO_0_ID_SD = 27
    GPIO_1_ID_SC = 28
    GPIO_2_SDA = 3
    GPIO_3_SCL = 5
    GPIO_4_GPCLK0 = 7
    GPIO_5 = 29
    GPIO_6 = 31
    GPIO_7_CE1 = 26
    GPIO_8_CE0 = 24
    GPIO_9_MISO = 21
    GPIO_10_MOSI = 19
    GPIO_11_SCLK = 23
    GPIO_12_PWM0 = 32
    GPIO_13_PWM1 = 33
    GPIO_14_TXD = 8
    GPIO_15_RXD = 10
    GPIO_16 = 36
    GPIO_17 = 11
    GPIO_18_PCM_CLK = 12
    GPIO_19_PCM_FS = 35
    GPIO_20_PCM_DIN = 38
    GPIO_21_PCM_DOUT = 40
    GPIO_22 = 15
    GPIO_23 = 16
    GPIO_24 = 18
    GPIO_25 = 22
    GPIO_26 = 37
    GPIO_27 = 13


class CkPin(IntEnum):
    """
    GPIO pins and their board pin numbers, corresponding to identifiers printed on the CanaKit GPIO extension board.
    """

    GPIO4 = Pin.GPIO_4_GPCLK0
    GPIO5 = Pin.GPIO_5
    GPIO6 = Pin.GPIO_6
    GPIO13 = Pin.GPIO_13_PWM1
    GPIO12 = Pin.GPIO_12_PWM0
    GPIO16 = Pin.GPIO_16
    GPIO17 = Pin.GPIO_17
    GPIO18 = Pin.GPIO_18_PCM_CLK
    GPIO19 = Pin.GPIO_19_PCM_FS
    GPIO20 = Pin.GPIO_20_PCM_DIN
    GPIO21 = Pin.GPIO_21_PCM_DOUT
    GPIO22 = Pin.GPIO_22
    GPIO23 = Pin.GPIO_23
    GPIO24 = Pin.GPIO_24
    GPIO25 = Pin.GPIO_25
    GPIO26 = Pin.GPIO_26
    GPIO27 = Pin.GPIO_27

    # SPI
    MOSI = Pin.GPIO_10_MOSI
    MISO = Pin.GPIO_9_MISO
    SCLK = Pin.GPIO_11_SCLK
    CE0 = Pin.GPIO_8_CE0
    CE1 = Pin.GPIO_7_CE1

    # UART
    TXD0 = Pin.GPIO_14_TXD
    RXD0 = Pin.GPIO_15_RXD

    # I2C
    SDA1 = Pin.GPIO_2_SDA
    SCL1 = Pin.GPIO_3_SCL

    # ID
    SDA0 = Pin.GPIO_0_ID_SD
    SCL0 = Pin.GPIO_1_ID_SC


def get_ck_pin(
        s: str
) -> CkPin:
    """
    Get CanaKit pin for a string.

    :param s: A type and name from either the `raspberry_py.gpio.Pin` class (e.g., Pin.GPIO_5) or the
    `raspberry_py.gpio.CkPin` class (e.g., CkPin.GPIO5).
    :return: CanaKit pin.
    """

    pin_type, pin_name = s.split('.')

    if pin_type == 'Pin':
        pin = Pin[pin_name]
        ck_pins = [
            p
            for p in CkPin
            if p.value == pin.value
        ]
        assert len(ck_pins) == 1
        ck_pin = ck_pins[0]
    elif pin_type == 'CkPin':
        ck_pin = CkPin[pin_name]
    else:
        raise ValueError(f'Unknown CanaKit pin:  {s}')

    return ck_pin


class Event:
    """
    Event.
    """

    def __init__(
            self,
            action: Callable[['Component.State'], None],
            trigger: Optional[Callable[['Component.State'], bool]] = None,
            synchronous: bool = True
    ):
        """
        Initialize the event.

        :param action: Function to run when event is triggered. Accepts the component's current state.
        :param trigger: A function that takes the component state and returns True if action should be triggered, or
        None to trigger the event on every state change.
        :param synchronous: Whether or not the action function should be called synchronously. If True, then execution
        will not resume until the action function has returned. If False, the action function will be started in a new
        thread and execution will resume immediately.
        """

        self.action = action
        self.trigger = trigger
        self.synchronous = synchronous


class Component(ABC):
    """
    Abstract base class for all components.
    """

    class State(ABC):
        """
        Abstract base class for all component states.
        """

        def __init__(
                self
        ):
            """
            Initialize the state.
            """

        @abstractmethod
        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

        def __ne__(
                self,
                other: object
        ) -> bool:
            """
            Check inequality with another state.

            :param other: State.
            :return: True if not equal and False otherwise.
            """

            return not self.__eq__(other)

        @abstractmethod
        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

    def event(
            self,
            action: Callable[['Component.State'], None],
            trigger: Optional[Callable[['Component.State'], bool]] = None,
            synchronous: bool = True
    ):
        """
        Add an event to the component. The event is triggered by state changes, which can be optionally filtered.

        :param action: Function to run when event is triggered. Accepts the component's current state.
        :param trigger: A function that takes the component state and returns True if action should be triggered, or
        None to trigger the event on every state change.
        :param synchronous: Whether the action function should be called synchronously. If True, then execution
        will not resume until the action function has returned. If False, the action function will be started in a new
        thread and execution will resume immediately.
        """

        self.events.append(Event(
            trigger=trigger,
            action=action,
            synchronous=synchronous
        ))

    def get_state(
            self
    ) -> 'Component.State':
        """
        Get the state.

        :return: State.
        """

        with self.state_lock:
            return self.state

    def set_state(
            self,
            state: 'Component.State'
    ):
        """
        Set the state and trigger events.

        :param state: State.
        """

        with self.state_lock:
            if state == self.state:
                logging.debug(f'State of {self} is already {state}. Not setting state or triggering events.')
            else:
                logging.debug(f'Setting state of {self} to {state}.')
                self.state = state
                for event in self.events:
                    if event.trigger is None or event.trigger(self.state):
                        if event.synchronous:
                            event.action(self.state)
                        else:
                            Thread(target=event.action, args=[self.state]).start()

    def __init__(
            self,
            state: 'Component.State'
    ):
        """
        Initialize the component.

        :param state: Initial state.
        """

        self.state = state

        self.events: List[Event] = []
        self.state_lock = RLock()
        self.id = str(uuid.uuid4())

    def __getstate__(
            self
    ) -> Dict:
        """
        Get state to picle.

        :return: State.
        """

        state = dict(self.__dict__)

        state['state_lock'] = None

        return state

    def __setstate__(
            self,
            state: Dict
    ):
        """
        Set state from pickle.

        :param state: State.
        """

        self.__dict__ = state

        self.state_lock = RLock()

    def __str__(
            self
    ) -> str:
        """
        Get string.

        :return: String.
        """

        return type(self).__name__


class Clock(Component):
    """
    A clock that ticks regularly.
    """

    class State(Component.State):
        """
        Clock state.
        """

        def __init__(
                self,
                running: bool,
                tick: int
        ):
            """
            Initialize the clock state.

            :param running: Whether the clock is running.
            :param tick: Clock tick.
            """

            self.running = running
            self.tick = tick

        def __eq__(
                self,
                other: object
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            if not isinstance(other, Clock.State):
                raise ValueError(f'Expected a {Clock.State}')

            return self.running == other.running and self.tick == other.tick

        def __str__(
                self
        ) -> str:
            """
            Get string.

            :return: String.
            """

            return f'running={self.running}, tick={self.tick}'

    def start(
            self
    ):
        """
        Start the clock.
        """

        self.state: Clock.State

        with self.state_lock:
            if self.state.running:
                logging.warning('Attempted to start clock that is running.')
            else:
                self.run_thread = Thread(target=self.__run__)
                self.run_thread.start()

    def stop(
            self
    ):
        """
        Stop the clock.
        """

        self.state: Clock.State

        with self.state_lock:
            if self.state.running:
                self.state.running = False
            else:
                logging.warning('Attempted to stop clock that is not running.')

        self.run_thread.join()

        logging.info('Stopped clock.')

    def __init__(
            self,
            tick_interval_seconds: Optional[float]
    ):
        """
        Initialize the clock.

        :param tick_interval_seconds: Number of seconds to wait between clock ticks, or None to tick as quickly as
        possible.
        """

        super().__init__(
            Clock.State(
                running=False,
                tick=0
            )
        )

        self.tick_interval_seconds = tick_interval_seconds

        self.run_thread: Optional[Thread] = None

    def __run__(
            self
    ):
        """
        Run the clock.
        """

        self.state: Clock.State

        # reset state
        with self.state_lock:
            new_state = deepcopy(self.state)
            new_state.running = True
            new_state.tick = 0
            self.set_state(new_state)

        # run until we should stop
        loop = True
        while loop:

            # sleep if we have a tick interval
            if self.tick_interval_seconds is not None:
                time.sleep(self.tick_interval_seconds)

            # watch out for race condition on the running value. only set state if we're still running.
            with self.state_lock:
                if self.state.running:
                    new_state = deepcopy(self.state)
                    new_state.tick += 1
                    self.set_state(new_state)
                else:
                    loop = False

        # set final state
        with self.state_lock:
            new_state = deepcopy(self.state)
            new_state.running = False
            self.set_state(new_state)
