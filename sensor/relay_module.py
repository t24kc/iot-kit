import RPi.GPIO as GPIO
from logging import getLogger, basicConfig, INFO
from time import sleep

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

DEFAULT_CHANNEL = 7


class RelayModule(object):
    def __init__(self, channel: int = DEFAULT_CHANNEL) -> None:
        """Relay Module Client Object.
        See: https://www.bitwizard.nl/wiki/Raspberry_Relay

        Args:
            channel: relay module default channel
        """
        self._channel = channel
        logger.info("relay module is starting...")

    def setup(self) -> None:
        """Setup relay module.
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self._channel, GPIO.OUT)

    def turn_on(self, turn_on_time: int) -> None:
        """Turn on relay module.

        Args:
            turn_on_time: time of turn on
        """
        logger.info(f"turn on relay module {turn_on_time} seconds.")
        GPIO.output(self._channel, 0)
        sleep(turn_on_time)
        self.cleanup()

    def turn_off(self) -> None:
        """Turn off relay module.
        """
        logger.info(f"turn off relay module.")
        GPIO.output(self._channel, 1)

    @staticmethod
    def cleanup():
        """Clean up relay module.
        """
        logger.info(f"cleanup relay module.")
        GPIO.cleanup()
