import smbus2
from logging import getLogger, basicConfig, INFO
from time import sleep

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

ADDRESS = 0x29

COMMAND_SYSTEM_FRESH_OUT_OF_RESET = 0x0016
COMMAND_SYSRANGE_START = 0x0018
COMMAND_RESULT_RANGE_VAL = 0x0062
COMMAND_SYSTEM_INTERRUPT_CLEAR = 0x0015
COMMAND_SYSALS_START = 0x0038
COMMAND_RESULT_ALS_VAL = 0x0050


class VL6180X(object):
    def __init__(self, address: int = ADDRESS) -> None:
        """Infrared Distance Sensor Client Object.
        See: https://www.st.com/ja/imaging-and-photonics-solutions/vl6180x.html

        Args:
            address: distance sensor address
        """
        self._address = address
        self._bus = smbus2.SMBus(1)

        if self.read(COMMAND_SYSTEM_FRESH_OUT_OF_RESET) == 1:
            self.write_byte(0x0207, 0x01)
            self.write_byte(0x0208, 0x01)
            self.write_byte(0x0096, 0x00)
            self.write_byte(0x0097, 0xFD)
            self.write_byte(0x00E3, 0x00)
            self.write_byte(0x00E4, 0x04)
            self.write_byte(0x00E5, 0x02)
            self.write_byte(0x00E6, 0x01)
            self.write_byte(0x00E7, 0x03)
            self.write_byte(0x00F5, 0x02)
            self.write_byte(0x00D9, 0x05)
            self.write_byte(0x00DB, 0xCE)
            self.write_byte(0x00DC, 0x03)
            self.write_byte(0x00DD, 0xF8)
            self.write_byte(0x009F, 0x00)
            self.write_byte(0x00A3, 0x3C)
            self.write_byte(0x00B7, 0x00)
            self.write_byte(0x00BB, 0x3C)
            self.write_byte(0x00B2, 0x09)
            self.write_byte(0x00CA, 0x09)
            self.write_byte(0x0198, 0x01)
            self.write_byte(0x01B0, 0x17)
            self.write_byte(0x01AD, 0x00)
            self.write_byte(0x00FF, 0x05)
            self.write_byte(0x0100, 0x05)
            self.write_byte(0x0199, 0x05)
            self.write_byte(0x01A6, 0x1B)
            self.write_byte(0x01AC, 0x3E)
            self.write_byte(0x01A7, 0x1F)
            self.write_byte(0x0030, 0x00)

        # Recommended : Public registers - See data sheet for more detail
        # Enables polling for 'New Sample ready' when measurement completes
        self.write_byte(0x0011, 0x10)
        # Set the averaging sample period (compromise between lower noise and increased execution time)
        self.write_byte(0x010A, 0x30)
        # Sets the light and dark gain (upper nibble). Dark gain should not be changed.
        self.write_byte(0x003F, 0x46)
        # sets the # of range measurements after which auto calibration of system is performed
        self.write_byte(0x0031, 0xFF)
        # Set ALS integration time to 100ms DocID026571 Rev 1 25/27 AN4545 SR03 settings27
        self.write_byte(0x0040, 0x63)
        # perform a single temperature calibration of the ranging sensor
        self.write_byte(0x002E, 0x01)

        # Optional: Public registers - See data sheet for more detail
        # Set default ranging inter-measurement period to 100ms
        self.write_byte(0x001B, 0x09)
        # Set default ALS inter-measurement period to 500ms
        self.write_byte(0x003E, 0x31)
        # Configures interrupt on 'New Sample Ready threshold event'
        self.write_byte(0x0014, 0x24)
        # change fresh out of set status to 0
        self.write_byte(0x016, 0x00)

        # Additional settings defaults from community
        # Sysrange max convergence time
        self.write_byte(0x001C, 0x32)
        # Sysrange range check enables
        self.write_byte(0x002D, 0x10 | 0x01)
        # Sysrange early convergence estimate
        self.write_byte16(0x0022, 0x7B)
        # Sysals integration period
        self.write_byte16(0x0040, 0x64)  # 100ms
        # sysals analogue gain
        self.write_byte(0x3F, 0x20)  # x40
        # firmware result scaler
        self.write_byte(0x0120, 0x01)

        logger.info("VL6180X sensor is starting...")

    def get_distance(self) -> float:
        """Read the range of an object in front of sensor and return it in mm.

        Returns:
            distance value
        """
        self.write_byte(COMMAND_SYSRANGE_START, 0x01)
        sleep(0.1)

        distance = self.read(COMMAND_RESULT_RANGE_VAL)
        self.write_byte(COMMAND_SYSTEM_INTERRUPT_CLEAR, 0x07)
        return distance

    def get_light(self) -> float:
        """Read the lux (light value) from the sensor and return it.

        Returns:
            lux value
        """
        self.write_byte(COMMAND_SYSALS_START, 0x01)
        sleep(0.5)

        light = self.read16(COMMAND_RESULT_ALS_VAL)
        self.write_byte(COMMAND_SYSTEM_INTERRUPT_CLEAR, 0x07)
        return light * 0.32 * 100 / (32 * 100)

    def read(self, register16: int) -> int:
        """Read and return a byte from the specified 16-bit register address.

        Args:
            register16: sensor register address

        Returns:
            Infrared Distance Sensor data.
        """
        a1 = (register16 >> 8) & 0xFF
        a0 = register16 & 0xFF

        self._bus.write_i2c_block_data(self._address, a1, [a0])
        return self._bus.read_byte(self._address)

    def read16(self, register16: int) -> int:
        """Read and return a 16-bit unsigned big endian value read from the specified 16-bit register address.

        Args:
            register16: sensor register address

        Returns:
            Infrared Distance Sensor data.
        """
        a1 = (register16 >> 8) & 0xFF
        a0 = register16 & 0xFF

        self._bus.write_i2c_block_data(self._address, a1, [a0])
        data16h = self._bus.read_byte(self._address)
        data16l = self._bus.read_byte(self._address)
        return (data16h << 8) | (data16l & 0xFF)

    def write_byte(self, register16: int, data: int) -> None:
        """Write 1 byte of data from the specified 16-bit register address.

        Args:
            register16: sensor register address
            data: write data
        """
        a1 = (register16 >> 8) & 0xFF
        a0 = register16 & 0xFF
        self._bus.write_i2c_block_data(self._address, a1, [a0, (data & 0xFF)])

    def write_byte16(self, register16: int, data16: int) -> None:
        """Write a 16-bit big endian value to the specified 16-bit register address.

        Args:
            register16: sensor register address
            data16: write data
        """
        a1 = (register16 >> 8) & 0xFF
        a0 = register16 & 0xFF
        d1 = (data16 >> 8) & 0xFF
        d0 = data16 & 0xFF
        self._bus.write_i2c_block_data(self._address, a1, [a0, d1, d0])


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Infrared Distance Sensor Script")
    parser.add_argument(
        "-i", "--interval", type=int, default=10, help="set script interval seconds"
    )
    args = parser.parse_args()

    sensor = VL6180X()
    while True:
        logger.info("Distance: {} mm".format(sensor.get_distance()))
        sleep(args.interval)


if __name__ == "__main__":
    main()
