import smbus2
from typing import Tuple, List, Sequence
from logging import getLogger, basicConfig, INFO
from time import sleep

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

ADDRESS = 0x44

COMMAND_MEAS_CLKST = 0x2C
COMMAND_MEAS_HIGHREP = [0x06]


class SHT31(object):
    def __init__(self, address: int = ADDRESS) -> None:
        """Temperature and Humidity Sensor Client Object.
        See: https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf

        Args:
            address: Temperature and Humidity Sensor address
        """
        self._address = address
        self._bus = smbus2.SMBus(1)
        logger.info("SHT31 sensor is starting...")

    def get_temperature(self) -> float:
        """Read the temperature from the sensor and return it.

        Returns:
            temperature value
        """
        temperature, humidity = self.get_temperature_humidity()
        return temperature

    def get_humidity(self) -> float:
        """Read the humidity from the sensor and return it.

        Returns:
            humidity value
        """
        temperature, humidity = self.get_temperature_humidity()
        return humidity

    def get_temperature_humidity(self) -> Tuple[float, float]:
        """Read the temperature, humidity from the sensor and return it.

        Returns:
            temperature, humidity value
        """
        self.write_list(COMMAND_MEAS_CLKST, COMMAND_MEAS_HIGHREP)
        sleep(0.5)

        data = self.read_list(0x00, 6)
        temperature = -45 + (175 * (data[0] * 256 + data[1]) / 65535.0)
        humidity = 100 * (data[3] * 256 + data[4]) / 65535.0

        return temperature, humidity

    def read(self, register: int) -> int:
        """Read and return a byte from the specified 16-bit register address.

        Args:
            register: sensor register address

        Returns:
            Temperature and Humidity Sensor data
        """
        return self._bus.read_byte_data(self._address, register) & 0xFF

    def read_list(self, register: int, length: int) -> List:
        """Read and return a byte list from the specified 16-bit register address.

        Args:
            register: sensor register address
            length: read byte length

        Returns:
            Temperature and Humidity Sensor data
        """
        return self._bus.read_i2c_block_data(self._address, register, length)

    def write(self, register: int, value: int) -> None:
        """Write 1 byte of data from the specified 16-bit register address.

        Args:
            register: sensor register address
            value: write data
        """
        value = value & 0xFF
        self._bus.write_byte_data(self._address, register, value)

    def write_list(self, register: int, data: Sequence[int]) -> None:
        """Write 1 byte of data from the specified 16-bit register address.

        Args:
            register: sensor register address
            data: write data
        """
        self._bus.write_i2c_block_data(self._address, register, data)


def debug() -> None:
    """debug function.
    """
    import argparse
    parser = argparse.ArgumentParser(
        description="Temperature and Humidity Sensor Script"
    )
    parser.add_argument(
        "-i", "--interval", type=int, default=10, help="set script interval seconds"
    )
    args = parser.parse_args()

    sensor = SHT31()
    while True:
        temperature, humidity = sensor.get_temperature_humidity()
        logger.info("Temperature: {} C, Humidity: {} %".format(temperature, humidity))
        sleep(args.interval)


if __name__ == "__main__":
    debug()
