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

    def __init__(self, use_decrypt: bool = False, device: str = "/dev/hidraw0") -> None:
        """CO2 Sensor Client Object.
        See: https://hackaday.io/project/5301-reverse-engineering-a-low-cost-usb-co-monitor/log/17909-all-your-base-are-belong-to-us

        Args:
            use_decrypt: use decrypt flag
            device: USB device path
        """
        self._use_decrypt = use_decrypt
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
            if self._use_decrypt:
                data = self._decrypt(data)

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


def debug() -> None:
    """debug function.
    """
    import argparse, os, yaml

    parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.chdir(parent_dir)
    with open("config.yaml") as f:
        config = yaml.full_load(f)

    parser = argparse.ArgumentParser(description="CO2 Sensor Script")
    parser.add_argument(
        "-i", "--interval", type=int, default=10, help="set script interval seconds"
    )
    args = parser.parse_args()

    sensor = CO2MINI(config["sensor"]["co2mini"]["decrypt"])
    while True:
        if sensor.read_data():
            logger.info("CO2: {} ppm".format(sensor.get_co2()))
        else:
            logger.error("Error!")
        sleep(args.interval)


if __name__ == "__main__":
    debug()
