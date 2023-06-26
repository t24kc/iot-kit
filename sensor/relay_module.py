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

    def turn_on(self, turn_on_minutes: int) -> None:
        """Turn on relay module.

        Args:
            turn_on_minutes: time of turn on (minutes)
        """
        logger.info(f"turn on relay module {turn_on_minutes} minutes.")
        GPIO.output(self._channel, 0)
        sleep(turn_on_minutes * 60)
        self.cleanup()

    def turn_off(self) -> None:
        """Turn off relay module.
        """
        logger.info("turn off relay module.")
        GPIO.output(self._channel, 1)

    @staticmethod
    def cleanup():
        """Clean up relay module.
        """
        logger.info("cleanup relay module.")
        GPIO.cleanup()


def debug() -> None:
    """debug function.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Relay module script")
    parser.add_argument(
        "-i", "--interval", type=int, default=0.2, help="set relay module turn on minutes"
    )
    args = parser.parse_args()

    relay_module = RelayModule()
    try:
        relay_module.setup()
        relay_module.turn_on(args.interval)
    except KeyboardInterrupt:
        relay_module.cleanup()


if __name__ == "__main__":
    debug()
