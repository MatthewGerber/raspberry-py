import logging
import time
from abc import ABC, abstractmethod
from copy import deepcopy
from threading import Thread
from typing import List, Tuple, Callable, Optional

import RPi.GPIO as gpio


def setup():
    """
    Set up the GPIO interface.
    :return:
    """

    gpio.setmode(gpio.BOARD)


def cleanup():
    """
    Clean up the GPIO interface.
    :return:
    """

    gpio.cleanup()


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
                other: 'Component.State'
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

        def __ne__(
                self,
                other: 'Component.State'
        ) -> bool:
            """
            Check inequality with another state.

            :param other: State.
            :return: True if not equal and False otherwise.
            """

            return not self.__eq__(other)

    def add_listener(
            self,
            trigger: Callable[['Component.State'], bool],
            event: Callable
    ):
        """
        Add a listener to the current component.

        :param trigger: A function that takes the current state and returns True if event should be fired.
        :param event: Event to fire if trigger returns True.
        """

        self.trigger_events.append((trigger, event))

    @abstractmethod
    def get(
            self
    ) -> 'Component.State':
        """
        Get the state.

        :return: State.
        """

    def set(
            self,
            state: 'Component.State'
    ):
        """
        Set the state and trigger any listeners.

        :param state: State.
        """

        if state != self.state:
            self.state = state
            for trigger, event in self.trigger_events:
                if trigger(self.state):
                    event()

    def __init__(
            self,
            state: 'Component.State'
    ):
        """
        Initialize the component.

        :param state: Initial state.
        """

        self.state = state

        self.trigger_events: List[Tuple[Callable[['Component.State'], bool], Callable]] = []


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
                other: 'Clock.State'
        ) -> bool:
            """
            Check equality with another state.

            :param other: State.
            :return: True if equal and False otherwise.
            """

            return self.running == other.running and self.tick == other.tick

    def get(
            self
    ) -> 'Clock.State':
        """
        Get the state.

        :return: State.
        """

        return self.state

    def start(
            self
    ):
        """
        Start the clock.
        """

        self.state: Clock.State

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

        if self.state.running:
            self.state.running = False
            self.run_thread.join()
            logging.info('Stopped clock.')
        else:
            logging.warning('Attempted to stop clock that is not running.')

    def __init__(
            self,
            tick_interval_seconds: float
    ):
        """
        Initialize the clock.

        :param tick_interval_seconds: Number of seconds to wait between clock ticks.
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
        new_state = deepcopy(self.state)
        new_state.running = True
        new_state.tick = 0
        self.set(new_state)

        # run until we should stop
        while self.state.running:

            # sleep for a bit
            time.sleep(self.tick_interval_seconds)

            # create new state
            new_state = deepcopy(self.state)
            new_state.tick += self.tick_interval_seconds

            # watch out for race condition on the running value. only set state if we're still running.
            if new_state.running:
                self.set(new_state)

        # set final state
        new_state = deepcopy(self.state)
        new_state.running = False
        self.set(new_state)
