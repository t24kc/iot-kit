import fcntl
import threading
import weakref
from logging import getLogger, basicConfig, INFO
from time import sleep
from typing import List

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
            decrypted = self._decrypt(data)

            if decrypted[4] != 0x0D or (sum(decrypted[:3]) & 0xFF) != decrypted[3]:
                logger.error(self._hd(data), " => ", self._hd(decrypted), "Checksum error")
            else:
                operation = decrypted[0]
                val = decrypted[1] << 8 | decrypted[2]
                self._values[operation] = val
            return True
        except Exception as e:
            logger.warning(e)
            return False

    def _decrypt(self, data: List) -> List:
        """Decrypt CO2 Sensor data.

        Args:
            data: Encrypted Sensor data

        Returns:
            Decrypted sensor data.
        """
        cstate = [0x48, 0x74, 0x65, 0x6D, 0x70, 0x39, 0x39, 0x65]
        shuffle = [2, 4, 0, 7, 1, 6, 5, 3]

        phase1 = [0] * 8
        for i, j in enumerate(shuffle):
            phase1[j] = data[i]

        phase2 = [0] * 8
        for i in range(8):
            phase2[i] = phase1[i] ^ self._key[i]

        phase3 = [0] * 8
        for i in range(8):
            phase3[i] = ((phase2[i] >> 3) | (phase2[(i - 1 + 8) % 8] << 5)) & 0xFF

        ctmp = [0] * 8
        for i in range(8):
            ctmp[i] = ((cstate[i] >> 4) | (cstate[i] << 4)) & 0xFF

        out = [0] * 8
        for i in range(8):
            out[i] = (0x100 + phase3[i] - ctmp[i]) & 0xFF

        return out

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
        return self._values[CO2METER_TEMP] / 16.0 - 273.15

    def get_humidity(self) -> float:
        """Get humidity data from sensor and return it.

        Returns:
            humidity value
        """
        # not implemented by all devices
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
