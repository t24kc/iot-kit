import cv2
from logging import getLogger, basicConfig, INFO
from datetime import datetime
from time import sleep

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

DEVICE_ID = 0


class WebCameraModule(object):
    def __init__(self, device_id: int = DEVICE_ID) -> None:
        """Web Camera Client Object.

        Args:
            device_id: device id
        """
        self._device_id = device_id
        logger.info("web camera module is starting...")

    def save_photo(self, save_path: str, with_datetime: bool = True) -> bool:
        """Save a web camera photo.

        Args:
            save_path: save web camera photo path
            with_datetime: with datetime text

        Returns:
            A boolean if success to save a web camera photo.
        """
        cap = cv2.VideoCapture(self._device_id)
        is_opened = cap.isOpened()
        if not is_opened:
            logger.error("Failed to open video capture.")
            return False
        sleep(2)

        result, img = cap.read()
        if not result:
            logger.error("Failed to read video capture.")
            return False
        if with_datetime:
            current_datetime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
            cv2.putText(img, current_datetime, (0, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3, cv2.LINE_AA)

        result = cv2.imwrite(save_path, img)
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Succeeded in saving a photo with web camera.")

        return result
