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
    def decode_fourcc(v) -> str:
        """Decode function to fourcc string.

        Args:
            v: frame fourcc number

        Returns:
            frame fourcc string
        """
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
        if "focus" in settings and settings["focus"]:
            cap.set(cv2.CAP_PROP_FOCUS, settings["focus"])

        logger.info(f"fourcc: {self.decode_fourcc(cap.get(cv2.CAP_PROP_FOURCC))}, width: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}, "
                    f"height: {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}, fps: {cap.get(cv2.CAP_PROP_FPS)}, focus: {cap.get(cv2.CAP_PROP_FOCUS)}")

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
        logger.info(f"Succeeded in saving a photo with web camera. save_path: {save_path}")

        return result


def debug() -> None:
    """debug function.
    """
    import argparse, os, yaml

    parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.chdir(parent_dir)
    with open(f"config.yaml") as f:
        config = yaml.full_load(f)

    parser = argparse.ArgumentParser(description="Web camera module script")
    parser.add_argument(
        "--fourcc", type=str, default=config["module"]["web_camera_module"]["settings"]["fourcc"],
        help="set video capture frame fourcc (MJPG, YUYV, H264, etc)"
    )
    parser.add_argument(
        "--width", type=int, default=config["module"]["web_camera_module"]["settings"]["width"],
        help="set video capture frame width (1280, 1920, 3840, etc)"
    )
    parser.add_argument(
        "--height", type=int, default=config["module"]["web_camera_module"]["settings"]["height"],
        help="set video capture frame height (720, 1080, 2160, etc)"
    )
    parser.add_argument(
        "--fps", type=int, default=config["module"]["web_camera_module"]["settings"]["fps"],
        help="set video capture frame fps (15, 30, 60, etc)"
    )
    parser.add_argument(
        "--focus", type=int, default=config["module"]["web_camera_module"]["settings"]["focus"],
        help="set video capture frame focus (0 ~ 255)"
    )
    args = parser.parse_args()

    settings = {"fourcc": args.fourcc, "width": args.width, "height": args.height, "fps": args.fps, "focus": args.focus}
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M")
    save_path = f"img/webcam_{current_datetime}.jpg"

    web_camera_module = WebCameraModule()
    web_camera_module.save_photo(save_path, settings)


if __name__ == "__main__":
    debug()
