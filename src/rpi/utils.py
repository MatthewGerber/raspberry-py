

def get_cpu_temp() -> float:
    """
    Get the current CPU temperature.

    :return: Temperature.
    """

    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        temp_celsius = float(f.read()) / 1000.0

    return temp_celsius
