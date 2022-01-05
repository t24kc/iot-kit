import smbus2
from typing import List
from logging import getLogger, basicConfig, INFO
from time import sleep

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

ADDRESS = 0x23

COMMAND_POWER_DOWN = 0x00
COMMAND_POWER_ON = 0x01
COMMAND_RESET = 0x07

# Start measurement at 4lx resolution. Time typically 16ms.
COMMAND_CONTINUOUS_LOW_RES_MODE = 0x13
# Start measurement at 1lx resolution. Time typically 120ms
COMMAND_CONTINUOUS_HIGH_RES_MODE_1 = 0x10
# Start measurement at 0.5lx resolution. Time typically 120ms
COMMAND_CONTINUOUS_HIGH_RES_MODE_2 = 0x11

# Device is automatically set to Power Down after measurement.
# Start measurement at 1lx resolution. Time typically 120ms
COMMAND_ONE_TIME_HIGH_RES_MODE_1 = 0x20
# Start measurement at 0.5lx resolution. Time typically 120ms
COMMAND_ONE_TIME_HIGH_RES_MODE_2 = 0x21
# Start measurement at 1lx resolution. Time typically 120ms
COMMAND_ONE_TIME_LOW_RES_MODE = 0x23


class BH1750FVI(object):
    def __init__(self, address: int = ADDRESS) -> None:
        """Digital Light Sensor Client Object.
        See: https://docs.rs-online.com/f199/0900766b81539909.pdf

        Args:
            address: digital light sensor address.
        """
        self._address = address
        self._bus = smbus2.SMBus(1)
        logger.info("BH1750 sensor is starting...")

    def _set_mode(self, mode: int) -> None:
        """Write command mode.

        Args:
            mode: command mode (COMMAND_POWER_ON, COMMAND_POWER_DOWN, COMMAND_RESET)
        """
        self.write(mode)

    def power_down(self) -> None:
        """Set digital light sensor to power down.
        """
        self._set_mode(COMMAND_POWER_DOWN)

    def power_on(self) -> None:
        """Set digital light sensor to power on.
        """
        self._set_mode(COMMAND_POWER_ON)

    def reset(self) -> None:
        """Reset digital light sensor.
        """
        self.power_on()
        self._set_mode(COMMAND_RESET)

    def get_light(self, command: int = COMMAND_ONE_TIME_HIGH_RES_MODE_1) -> float:
        """Read the lux (light value) from the sensor and return it.

        Args:
            command: one time command

        Returns:
            Digital light sensor lux.
        """
        light = self.read(command)
        return self.convert_to_number(light)

    def read(self, register: int) -> List:
        """Read digital light sensor data.

        Args:
            register: command

        Returns:
            Digital light sensor data.
        """
        return self._bus.read_i2c_block_data(self._address, register, 2)

    def write(self, register: int) -> None:
        """Write byte digital light sensor.

        Args:
            register: command
        """
        self._bus.write_byte(self._address, register)

    @staticmethod
    def convert_to_number(data: List) -> float:
        """Simple function to convert 2 bytes of data into a decimal number.

        Args:
            data: sensor data list.

        Returns:
            convert to number from sensor data list.
        """
        return (data[1] + (256 * data[0])) / 1.2


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Digital Light Sensor Script")
    parser.add_argument(
        "-i", "--interval", type=int, default=10, help="set script interval seconds"
    )
    args = parser.parse_args()

    sensor = BH1750FVI()
    while True:
        logger.info("Light Level (1x gain): {} lux".format(sensor.get_light()))
        sleep(args.interval)


if __name__ == "__main__":
    main()
