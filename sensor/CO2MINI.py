import fcntl
import threading
import weakref
from logging import getLogger, basicConfig, INFO
from time import sleep

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

CO2METER_CO2 = 0x50
CO2METER_TEMP = 0x42
CO2METER_HUM = 0x44
HIDIOCSFEATURE_9 = 0xC0094806


class CO2MINI(object):
    _key = [0xC4, 0xC6, 0xC0, 0x92, 0x40, 0x23, 0xDC, 0x96]

    def __init__(self, device: str = "/dev/hidraw0") -> None:
        """CO2 Sensor Client Object.
        See: https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us

        Args:
            device: USB device path
        """
        self._values = {CO2METER_CO2: 0, CO2METER_TEMP: 0, CO2METER_HUM: 0}
        self._file = open(device, "a+b", 0)

        set_report = [0] + self._key
        fcntl.ioctl(self._file, HIDIOCSFEATURE_9, bytearray(set_report))

        thread = threading.Thread(target=self._co2_worker, args=(weakref.ref(self),))
        thread.daemon = True
        thread.start()

        logger.info("CO2MINI sensor is starting...")

    @staticmethod
    def _co2_worker(weak_self) -> None:
        """Worker for read co2 data.

        Args:
            weak_self: weakref object
        """
        while True:
            self = weak_self()
            if self is None:
                break
            self.read_data()

    def read_data(self) -> bool:
        """Read CO2 Sensor data.

        Returns:
            Whether read data was possible.
        """
        try:
            data = list(self._file.read(8))

            if data[4] != 0x0D or (sum(data[:3]) & 0xFF) != data[3]:
                logger.error(f"Checksum error: {self._hd(data)}.")
            else:
                operation = data[0]
                val = data[1] << 8 | data[2]
                self._values[operation] = val
            return True
        except Exception as e:
            logger.warning(e)
            return False

    @staticmethod
    def _hd(data) -> str:
        """Helper function for printing the raw data.

        Args:
            data: sensor list data

        Returns:
            sensor string data.
        """
        return " ".join("%02X" % e for e in data)

    def get_co2(self) -> float:
        """Get CO2 data from sensor and return it.

        Returns:
            co2 value
        """
        return self._values[CO2METER_CO2]

    def get_temperature(self) -> float:
        """Get temperature data from sensor and return it.

        Returns:
            temperature value
        """
        if CO2METER_TEMP not in self._values:
            logger.error("Temperature not exists in data.")
            return 0
        return self._values[CO2METER_TEMP] / 16.0 - 273.15

    def get_humidity(self) -> float:
        """Get humidity data from sensor and return it.

        Returns:
            humidity value
        """
        # not implemented by all devices
        if CO2METER_HUM not in self._values:
            logger.error("Humidity not exists in data.")
            return 0
        return self._values[CO2METER_HUM] / 100.0


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CO2 Sensor Script")
    parser.add_argument(
        "-i", "--interval", type=int, default=10, help="set script interval seconds"
    )
    args = parser.parse_args()

    sensor = CO2MINI()
    while True:
        if sensor.read_data():
            logger.info("CO2: {} ppm".format(sensor.get_co2()))
        else:
            logger.error("Error!")
        sleep(args.interval)


if __name__ == "__main__":
    main()
