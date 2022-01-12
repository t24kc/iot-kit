import cv2
from logging import getLogger, basicConfig, INFO
from datetime import datetime
from time import sleep
from typing import Dict, Optional

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

    @staticmethod
    def decode_fourcc(v):
        v = int(v)
        return "".join([chr((v >> 8 * i) & 0xFF) for i in range(4)])

    def save_photo(self, save_path: str, settings: Optional[Dict] = None, with_datetime: bool = True) -> bool:
        """Save a web camera photo.

        Args:
            save_path: save web camera photo path
            settings: video capture frame settings
            with_datetime: with datetime text

        Returns:
            A boolean if success to save a web camera photo.
        """
        cap = cv2.VideoCapture(self._device_id)
        if "fourcc" in settings and settings["fourcc"]:
            c1, c2, c3, c4 = list(settings["fourcc"])
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(c1, c2, c3, c4))
        if "width" in settings and settings["width"]:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings["width"])
        if "height" in settings and settings["height"]:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["height"])
        if "fps" in settings and settings["fps"]:
            cap.set(cv2.CAP_PROP_FPS, settings["fps"])

        logger.info(f"fourcc: {self.decode_fourcc(cap.get(cv2.CAP_PROP_FOURCC))}, width: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}, "
                    f"height: {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}, fps: {cap.get(cv2.CAP_PROP_FPS)}")

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
