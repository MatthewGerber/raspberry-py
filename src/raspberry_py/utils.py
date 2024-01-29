from typing import Optional


def get_cpu_temp() -> float:
    """
    Get the current CPU temperature.

    :return: Temperature.
    """

    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        temp_celsius = float(f.read()) / 1000.0

    return temp_celsius


class IncrementalSampleAverager:
    """
    An incremental, constant-time and -memory sample averager. Supports both decreasing (i.e., unweighted sample
    average) and constant (i.e., exponential recency-weighted average) step sizes.
    """

    def reset(
            self
    ):
        """
        Reset the average and number of samples.
        """

        self.average = self.initial_value
        self.n = 0

    def update(
            self,
            value: float,
            weight: Optional[float] = None
    ):
        """
        Update the sample average with a new value.

        :param value: New value.
        :param weight: Weight of the value. This is a generalization of the following cases:

          * constant weight for all samples:  recency-weighted average (see `alpha` in the constructor).
          * 1 / n:  standard average.
          * else:  arbitrary weighting scheme.

        If `weighted` was True in the constructor, then a non-None value must be passed here.
        """

        if weight is not None and not self.weighted:
            raise ValueError('Cannot pass a weight to an unweighted averager.')

        self.n += 1

        if self.has_alpha:
            step_size = self.alpha
        elif self.weighted:

            if weight is None:
                raise ValueError('The averager is weighted, so non-None values must be passed for weight.')

            self.cumulative_weight += weight
            step_size = weight / self.cumulative_weight

        else:
            step_size = 1 / self.n

        self.average = self.average + step_size * (value - self.average)

    def get_value(
            self
    ) -> float:
        """
        Get current average value.

        :return: Average.
        """

        return self.average

    def __init__(
            self,
            initial_value: float = 0.0,
            alpha: float = None,
            weighted: bool = False
    ):
        """
        Initialize the averager.

        :param initial_value: Initial value of the averager.
        :param alpha: Constant step-size value. If provided, the sample average becomes a recency-weighted average with
        the weight of previous values decreasing according to `alpha^i`, where `i` is the number of samples prior to
        the current when a previous value was obtained. If `None` is passed, then the unweighted sample average will be
        used, and every value will have the same weight.
        :param weighted: Whether or not per-value weights will be provided to calls to `update`. If this is True, then
        every call to `update` must provide a non-None value for `weight`.
        """

        if alpha is not None:
            if alpha <= 0:
                raise ValueError('alpha must be > 0')
            elif weighted:
                raise ValueError('Cannot supply alpha and per-value weights.')

        self.initial_value = initial_value
        self.alpha = alpha
        self.has_alpha = self.alpha is not None
        self.weighted = weighted
        self.cumulative_weight = 0.0 if self.weighted else None
        self.average = initial_value
        self.n = 0

    def __str__(
            self
    ) -> str:
        """
        Get string.

        :return: String.
        """

        return str(self.average)

    def __eq__(
            self,
            other: object
    ) -> bool:
        """
        Check equality.

        :param other: Other value.
        :return: True if average values match and False otherwise.
        """

        if isinstance(other, IncrementalSampleAverager):
            result = self.get_value() == other.get_value()
        elif isinstance(other, float):
            result = self.get_value() == other
        else:
            raise ValueError(f'Expected a {IncrementalSampleAverager} or {float}')

        return result

    def __ne__(
            self,
            other: object
    ) -> bool:
        """
        Check inequality.

        :param other: Other value.
        :return: True if average values do not match and False otherwise.
        """

        return not (self == other)

    def __gt__(
            self,
            other: object
    ):
        """
        Check greater than.

        :param other: Other value.
        :return: True if the current value is greater.
        """

        if isinstance(other, IncrementalSampleAverager):
            result = self.get_value() > other.get_value()
        elif isinstance(other, float):
            result = self.get_value() > other
        else:
            raise ValueError(f'Expected a {IncrementalSampleAverager} or {float}')

        return result

    def __ge__(
            self,
            other: object
    ):
        """
        Check greater than or equal.

        :param other: Other value.
        :return: True if the current value is greater than or equal.
        """

        return (self > other) or (self == other)

    def __lt__(
            self,
            other: object
    ):
        """
        Check less than.

        :param other: Other value.
        :return: True if the current value is less than.
        """

        if isinstance(other, IncrementalSampleAverager):
            result = self.get_value() < other.get_value()
        elif isinstance(other, float):
            result = self.get_value() < other
        else:
            raise ValueError(f'Expected a {IncrementalSampleAverager} or {float}')

        return result

    def __le__(
            self,
            other: object
    ):
        """
        Check less than or equal.

        :param other: Other value.
        :return: True if the current value is less than or equal.
        """

        return (self < other) or (self == other)

    def __format__(
            self,
            format_spec: str
    ) -> str:
        """
        Format the current value.

        :param format_spec: Format specification.
        :return: String.
        """

        # noinspection PyStringFormat
        return f'{{:{format_spec}}}'.format(self.get_value())
