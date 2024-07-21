import argparse
import os
import yaml
import requests
import schedule
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Optional
from logging import getLogger, basicConfig, INFO
from datetime import datetime, timedelta
from time import sleep

from lib.mail import Mail
from lib.photo_library import PhotoLibrary
from lib.spread_sheet import SpreadSheet

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)


class Scheduler(object):
    params_mapping = {
        "time": {"name": "Time", "type": "datetime64[ns]", "unit": ""},
        "light": {"name": "Light(lux)", "type": float, "unit": "lux"},
        "temperature": {"name": "Temperature(C)", "type": float, "unit": "C"},
        "humidity": {"name": "Humidity(%)", "type": float, "unit": "%"},
        "co2": {"name": "CO2(ppm)", "type": float, "unit": "ppm"},
        "distance": {"name": "Distance(mm)", "type": float, "unit": "mm"},
        "power_flag": {"name": "PowerFlag", "type": int, "unit": ""},
    }

    def __init__(self, config: Dict) -> None:
        """Scheduler Job Object.

        Args:
            config: config yaml file data
        """
        self._config = config

        # IoT sensor, module
        if self.is_use_flag("module", "relay_module", "scheduler") or self.is_use_flag("module", "relay_module", "conditions"):
            from sensor.relay_module import RelayModule
            self._relay_module = RelayModule()
        if self.is_use_flag("module", "web_camera_module"):
            from sensor.web_camera_module import WebCameraModule
            self._web_camera_module = WebCameraModule()
        if self.is_use_flag("sensor", "bh1750fvi"):
            from sensor.BH1750FVI import BH1750FVI
            self._bh1750fvi_sensor = BH1750FVI()
        if self.is_use_flag("sensor", "sht31"):
            from sensor.SHT31 import SHT31
            self._sht31_sensor = SHT31()
        if self.is_use_flag("sensor", "co2mini"):
            from sensor.CO2MINI import CO2MINI
            self._co2mini_sensor = CO2MINI(self._config["sensor"]["co2mini"]["decrypt"])
        if self.is_use_flag("sensor", "vl6180"):
            from sensor.VL6180 import VL6180X
            self._vl6180x_sensor = VL6180X()
        self._init_params()
        self._init_interval_minutes()

        # Google Service
        self._spread_sheet_client = SpreadSheet(
            self._config["google"]["default"]["service_account_path"],
            self._config["google"]["spread_sheet"]["id"],
        )
        self._photo_library_client = PhotoLibrary(
            self._config["google"]["default"]["client_secrets_path"],
            self._config["google"]["photo_library"]["token_path"],
        )
        self._mail_client = Mail(
            self._config["google"]["default"]["client_secrets_path"],
            self._config["google"]["mail"]["token_path"],
        )
        self._init_spread_sheet()

    def is_use_flag(self, *args) -> bool:
        """Get whether the use flag is set.

        Args:
            *args: args

        Returns:
            A boolean if the use flag is set.
        """
        assert(len(args) >= 2), "args must be set to 2 or more."

        tmp_config = self._config
        for arg in args:
            tmp_config = tmp_config[arg]

        return tmp_config["use"]

    def _init_params(self) -> None:
        """Initialize the parameters of use.
        """
        # expected: value, function
        self._params = {}
        # The value of the upper sensor has priority
        if self.is_use_flag("sensor", "bh1750fvi"):
            if "light" not in self._params:
                self._params["light"] = {"value": 0, "average":0, "min":0, "max":0, "count":0, "function": self._bh1750fvi_sensor.get_light}
        if self.is_use_flag("sensor", "sht31"):
            if "temperature" not in self._params:
                self._params["temperature"] = {"value": 0, "average":0, "min":0, "max":0, "count":0, "function": self._sht31_sensor.get_temperature}
            if "humidity" not in self._params:
                self._params["humidity"] = {"value": 0, "average":0, "min":0, "max":0, "count":0, "function": self._sht31_sensor.get_humidity}
        if self.is_use_flag("sensor", "co2mini"):
            if "temperature" not in self._params:
                self._params["temperature"] = {"value": 0, "average":0, "min":0, "max":0, "count":0, "function": self._co2mini_sensor.get_temperature}
            if "humidity" not in self._params:
                self._params["humidity"] = {"value": 0, "average":0, "min":0, "max":0, "count":0, "function": self._co2mini_sensor.get_humidity}
            if "co2" not in self._params:
                self._params["co2"] = {"value": 0, "average":0, "min":0, "max":0, "count":0, "function": self._co2mini_sensor.get_co2}
        if self.is_use_flag("sensor", "vl6180"):
            if "light" not in self._params:
                self._params["light"] = {"value": 0,  "average":0, "min":0, "max":0, "count":0,"function": self._vl6180x_sensor.get_light}
            if "distance" not in self._params:
                self._params["distance"] = {"value": 0, "average":0, "min":0, "max":0, "count":0, "function": self._vl6180x_sensor.get_distance}

    def _init_interval_minutes(self) -> None:
        """Initialize the skip interval minutes of use.
        """
        self._interval_minutes = {
            "relay_module": 0,
            "alert_mail": {key: 0 for key in self._params.keys()}
        }

    def _init_spread_sheet(self) -> None:
        """Initialize the spreadsheet.
        """
        if not self.is_use_flag("google", "spread_sheet"):
            return
        used_params = [self.params_mapping[key]["name"] for key in self._get_params_key_list()]
        if not used_params:
            return
        entered_params = self._spread_sheet_client.row_values(1)
        if used_params == entered_params:
            return

        if entered_params:
            self._spread_sheet_client.clear()
        self._spread_sheet_client.append_row(used_params)

    def _get_params_key_list(self) -> List:
        """Get the parameters key list of use.

        Returns:
            the parameters key list of use.
        """
        if not self._params:
            return []

        used_params = ["time"] + list(self._params.keys())
        if self.is_use_flag("module", "relay_module", "conditions"):
            used_params.append("power_flag")

        return used_params

    def monitoring_job(self) -> None:
        """Create the monitoring job.
        """
        self._reduce_interval_minutes()
        self._fetch_params()
        self._logging_spread_sheet()
        if self._is_power_flag():
            self._turn_on_power()
        if self._is_alert_flag():
            self._alert_mail()

    def _reduce_interval_minutes(self) -> None:
        """Reduce the skip interval minutes of use.
        """
        interval_minutes = self._config["sensor"]["scheduler"]["interval_minutes"]
        self._interval_minutes["relay_module"] = max(0, self._interval_minutes["relay_module"] - interval_minutes)
        for key in self._params.keys():
            self._interval_minutes["alert_mail"][key] = max(0, self._interval_minutes["alert_mail"][key] - interval_minutes)

    def _fetch_params(self) -> None:
        """Fetch the parameters of use by user callback function.
        """
        for key, data in self._params.items():
            sensor = self._params[key]["function"]()
            average = self._params[key]["average"]
            count = self._params["count"]
            max = self._params["max"]
            min = self._params["min"]

            self._params[key]["value"] = sensor
            self._params[key]["average"] = (average * count + sensor)/(count + 1)
            self._params[key]["count"] = count + 1

            if count == 0 or max < sensor :
                self._params["max"] = sensor
            if count == 0 or sensor < min :
                self._params["min"] = sensor





    def _logging_spread_sheet(self) -> None:
        """Log the parameters log to spreadsheet.
        """
        if not self.is_use_flag("google", "spread_sheet"):
            return
        if not self._params:
            return

        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 配列の連＆リスト内包表記
        # [時間,温度,湿度,...]みたくなる
        append_rows = [current_datetime] + [round(self._params[key]["value"], 1) for key in self._params.keys()]
        if self.is_use_flag("module", "relay_module", "conditions"):
            append_rows.append(int(self._is_power_flag()))

        self._spread_sheet_client.append_row(append_rows)

    def _is_power_flag(self) -> bool:
        """Get whether the power flag.

        Returns:
            A boolean if the power flag.
        """
        if not self.is_use_flag("module", "relay_module", "conditions"):
            return False
        if self._interval_minutes["relay_module"] > 0:
            return False

        for conditions_filter in self._config["module"]["relay_module"]["conditions"]["filters"]:
            filter_name = conditions_filter["name"]
            if filter_name not in self._params:
                continue

            sensor_value = self._params[filter_name]["value"]
            filter_threshold = conditions_filter["threshold"]
            if conditions_filter["limit"] == "upper" and sensor_value >= filter_threshold:
                return True
            if conditions_filter["limit"] == "lower" and sensor_value <= filter_threshold:
                return True

        return False

    def _turn_on_power(self) -> None:
        """Turn on power by relay module.
        """
        if not self.is_use_flag("module", "relay_module", "scheduler") \
                and not self.is_use_flag("module", "relay_module", "conditions"):
            return

        self._relay_module.setup()
        self._relay_module.turn_on(self._config["module"]["relay_module"]["turn_on_minutes"])
        self._interval_minutes["relay_module"] = self._config["module"]["relay_module"]["conditions"]["skip_interval_minutes"]

    def turn_off_power(self) -> None:
        """Turn off power by relay module.
        """
        if not self.is_use_flag("module", "relay_module", "scheduler") \
                and not self.is_use_flag("module", "relay_module", "conditions"):
            return

        self._relay_module.turn_off()

    def cleanup(self) -> None:
        """cleanup by relay module.
        """
        if not self.is_use_flag("module", "relay_module", "scheduler") \
                and not self.is_use_flag("module", "relay_module", "conditions"):
            return

        self._relay_module.cleanup()

    def _is_alert_flag(self) -> bool:
        """Get whether the alert flag.

        Returns:
            A boolean if the alert flag.
        """
        if not self.is_use_flag("google", "mail", "alert"):
            return False

        for alert_filter in self._config["google"]["mail"]["alert"]["filters"]:
            filter_name = alert_filter["name"]
            if filter_name not in self._params:
                continue
            if self._interval_minutes["alert_mail"][filter_name] > 0:
                continue

            sensor_value = self._params[filter_name]["value"]
            filter_threshold = alert_filter["threshold"]
            if alert_filter["limit"] == "upper" and sensor_value >= filter_threshold:
                return True
            if alert_filter["limit"] == "lower" and sensor_value <= filter_threshold:
                return True

        return False

    def _alert_mail(self) -> None:
        """Send an alert email with the parameters that exceed the threshold.
        """
        if not self.is_use_flag("google", "mail", "alert"):
            return

        body = ""
        alert_mail_interval = self._config["google"]["mail"]["alert"]["skip_interval_minutes"]
        for alert_filter in self._config["google"]["mail"]["alert"]["filters"]:
            filter_name = alert_filter["name"]
            if filter_name not in self._params:
                continue
            if self._interval_minutes["alert_mail"][filter_name] > 0:
                continue

            sensor_value = round(self._params[filter_name]["value"], 1)
            filter_threshold = alert_filter["threshold"]
            if alert_filter["limit"] == "upper" and sensor_value >= filter_threshold:
                body += self._config["google"]["mail"]["alert"]["body"]["upper"].format(
                    name=filter_name.capitalize(),
                    threshold=filter_threshold,
                    value=sensor_value,
                    unit=self.params_mapping[filter_name]["unit"]
                ) + "\n"
                self._interval_minutes["alert_mail"][filter_name] = alert_mail_interval
            if alert_filter["limit"] == "lower" and sensor_value <= filter_threshold:
                body += self._config["google"]["mail"]["alert"]["body"]["lower"].format(
                    name=filter_name.capitalize(),
                    threshold=filter_threshold,
                    value=sensor_value,
                    unit=self.params_mapping[filter_name]["unit"]
                ) + "\n"
                self._interval_minutes["alert_mail"][filter_name] = alert_mail_interval

        if body:
            body += self._append_google_link_body(with_spread_sheet=True)
            self._send_mail(self._config["google"]["mail"]["alert"]["subject"], body)

    def _append_google_link_body(self, with_spread_sheet: bool = False, with_photo_library: bool = False) -> str:
        """Get Google service link urls for email message.

        Args:
            with_spread_sheet: with spreadsheets url
            with_photo_library: with photo library url

        Returns:
            A email body message with Google service link.
        """
        body = "\n"
        if with_spread_sheet and self.is_use_flag("google", "spread_sheet"):
            body += f"spreadsheets: https://docs.google.com/spreadsheets/d/{self._config['google']['spread_sheet']['id']}/edit\n"
        if with_photo_library and self.is_use_flag("google", "photo_library"):
            album_title = self._config["google"]["photo_library"]["album_title"]
            album = self._photo_library_client.get_album(album_title)
            if album:
                body += f"photo_library: {album['productUrl']}\n"

        return body

    def _send_mail(self, subject: str, body: str, image_file_list: Optional[List[str]] = None) -> None:
        """Send the email.

        Args:
            subject: message subject
            body: message body
            image_file_list: sending image file path
        """
        if not self.is_use_flag("google", "mail", "summary") and not self.is_use_flag("google", "mail", "alert"):
            return

        if image_file_list:
            for image_file in image_file_list:
                assert os.path.isfile(image_file), "image not found."
            message = self._mail_client.create_message_with_image(
                self._config["google"]["mail"]["to_address"], subject, body, image_file_list
            )
        else:
            message = self._mail_client.create_message(
                self._config["google"]["mail"]["to_address"], subject, body
            )

        self._mail_client.send_message(message)
        logger.info(body)

    def summary_mail_job(self) -> None:
        """Create the summary email job.
        """
        if not self.is_use_flag("google", "mail", "summary") and \
                (not self.is_use_flag("google", "spread_sheet") and not self.is_use_flag("google", "photo_library")):
            return

        graph_image_path = f"{self._config['google']['photo_library']['img_dir']}/graph.jpg"
        self._save_summary_graph(graph_image_path)
        image_file_list = [graph_image_path]

        photo_image_path_list = self._save_photo_image()
        image_file_list.extend(photo_image_path_list)

        from_days = self._config["google"]["mail"]["summary"]["from_days"]
        body = self._config["google"]["mail"]["summary"]["body"]["title"].format(from_days=from_days) + "\n"

        for key, data in self._params.items():
            body += self._config["google"]["mail"]["summary"]["body"]["contents"].format(sensor=key, average=self._params[key]["average"], max=self._params["max"], min=self._params["min"])+"\n"


        body += self._append_google_link_body(with_spread_sheet=True, with_photo_library=True)
        self._send_mail(
            self._config["google"]["mail"]["summary"]["subject"],
            body,
            image_file_list,
        )

        for image_path in image_file_list:
            os.remove(image_path)

    def _save_summary_graph(self, graph_image_path: str) -> bool:
        """Create the summary parameters graph image.

        Args:
            graph_image_path: saving graph image path

        Returns:
            Returns whether the parameters graph image could be saved.
        """
        if not self.is_use_flag("google", "spread_sheet"):
            return False

        history_df = self._get_history_dataframe()

        kwargs = {"kind": "line", "legend": False, "use_index": True, "rot": 45}
        setting_list = []
        for key in list(self._params.keys())[:5]:
            y = self.params_mapping[key]["name"]
            setting_list.append({"title": y, "x": "Time", "y": y})

        params_len = len(self._params)
        num_cols, num_rows = 1, 1
        if params_len >= 5:
            num_cols, num_rows = 3, 2
        elif params_len == 4:
            num_cols, num_rows = 2, 2
        elif params_len == 3:
            num_rows = 3
        elif params_len == 2:
            num_rows = 2

        fig, axes = plt.subplots(ncols=num_cols, nrows=num_rows, sharex="col", figsize=(15, 10))
        if params_len == 5:
            axes[1][2].set_visible(False)

        for ax, setting in zip(axes.ravel(), setting_list):
            history_df.plot(
                setting["x"], setting["y"], ax=ax, title=setting["title"], **kwargs
            )

        fig.tight_layout()
        plt.savefig(graph_image_path)
        return True

    def _get_history_dataframe(self) -> Optional[pd.DataFrame]:
        """Get the parameters' history dataframe by spreadsheet.

        Returns:
            Dataframe of the diff days parameters' history.
        """
        if not self.is_use_flag("google", "spread_sheet"):
            return

        history_df = pd.DataFrame(self._spread_sheet_client.get_all_values())
        history_df.columns = list(history_df.iloc[0])
        history_df.drop(0, axis=0, inplace=True)
        history_df = history_df.astype(
            {
                self.params_mapping[key]["name"]: self.params_mapping[key]["type"] for key in self._get_params_key_list()
            }
        )

        # ================================================サマライズ期間の取得はここ=====================================================
        target_date = (datetime.now() - timedelta(days=self._config["google"]["mail"]["summary"]["from_days"])).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return history_df.query(f"Time > '{target_date}'").reset_index(drop=True)

    def _save_photo_image(self) -> List:
        """Save Google Photo image to local storage and return the path list.

        Returns:
            Google Photo image path list
        """
        image_file_list = []
        if not self.is_use_flag("google", "photo_library"):
            return image_file_list

        album_id = self._get_album_id()
        filter_date_list = []

        # ================過去~日分の日付文字列を配列に格納 現在の日付から「日」までを見てる（%Y%m%d"）=====================
        for days in range(self._config["google"]["mail"]["summary"]["from_days"]):
            filter_date_list.append((datetime.now() - timedelta(days=days)).strftime("%Y%m%d"))
        media_dict = self._photo_library_client.get_media_dict(
            album_id, filter_name=f"webcam_({'|'.join(filter_date_list)})"
        )

        if not media_dict:
            return image_file_list

        sorted_name_list = sorted(media_dict.keys())

        # ==============================最新の画像と最古の画像を指定=================================
        if len(sorted_name_list) == 1:
            target_name_list = [sorted_name_list[0]]
        else:
            target_name_list = [sorted_name_list[0], sorted_name_list[-1]]

        for filename in target_name_list:
            response = requests.get(media_dict[filename]["base_url"])
            assert response.status_code == 200
            # imgフォルダに保存
            photo_image_path = f"{self._config['google']['photo_library']['img_dir']}/{filename}"
            with open(photo_image_path, "wb") as f:
                f.write(response.content)
            image_file_list.append(photo_image_path)

        # [img/webcam_yyyymmdd, img/webcam_yyyymmdd]みたいな感じの配列（ローカルのパス）
        return image_file_list

    def relay_module_job(self) -> None:
        """Create the relay module job to turn on power.
        """
        if not self.is_use_flag("module", "relay_module", "scheduler"):
            return

        self._turn_on_power()

    def web_camera_module_job(self) -> None:
        """Create the web camera module job to take a photo.
        """
        if not self.is_use_flag("module", "web_camera_module"):
            return

        current_datetime = datetime.now().strftime("%Y%m%d_%H%M")
        photo_image_path = f"{self._config['google']['photo_library']['img_dir']}/webcam_{current_datetime}.jpg"
        settings = self._config["module"]["web_camera_module"]["settings"]
        result = self._web_camera_module.save_photo(photo_image_path, settings)
        if not result or not self.is_use_flag("google", "photo_library"):
            return

        album_id = self._get_album_id()
        self._photo_library_client.upload_image(album_id, photo_image_path)

        os.remove(photo_image_path)
        logger.info(f"Succeeded removed a photo. remove_path: {photo_image_path}")

    def _get_album_id(self) -> Optional[str]:
        """Get the target album id.

        Returns:
            Album ID
        """
        if not self.is_use_flag("google", "photo_library"):
            return

        album_title = self._config["google"]["photo_library"]["album_title"]
        album = self._photo_library_client.get_album(album_title)
        if album:
            album_id = album["id"]
        else:
            album_id = self._photo_library_client.create_album(album_title)

        return album_id


    def logging_avg_job(self) -> None:
        """Logging the average etc to spreadsheet
        """
        if not self.is_use_flag("google", "spread_sheet"):
            return
        if not self._params:
            return

        target_date = datetime.now()-timedelta(1) #昨日
        target_date_format = target_date.strftime("%Y-%m-%d %H:%M:%S")
        append_rows = [target_date_format] + [round(self._params[key]["average"], 1) for key in self._params.keys()]

        # ここどういう意味か聞く
        # if self.is_use_flag("module", "relay_module", "conditions"):
        #     append_rows.append(int(self._is_power_flag()))

        # append_rowの2個目の引数で二枚目のシートを指定
        self._spread_sheet_client.append_row(append_rows,1)
        for key in self._params.keys():
            self._params[key]["average"] = 0
            self._params[key]["count"] = 0






def main() -> None:
    """main function.
    """
    config = _full_load_config()

    scheduler = Scheduler(config)
    _create_scheduler_job(scheduler.monitoring_job, config["sensor"]["scheduler"])
    #追記
    #他に合わせてconfigから持ってくるパターン
    # _create_scheduler_job(scheduler.logging_avg_job, config["avgjob"]["scheduler"])
    #毎日で固定するパターン
    schedule.every().day.at("00:00:00").do(scheduler.logging_avg_job)
    if scheduler.is_use_flag("google", "mail", "summary"):
        _create_scheduler_job(scheduler.summary_mail_job, config["google"]["mail"]["summary"]["scheduler"])
    if scheduler.is_use_flag("module", "relay_module", "scheduler"):
        _create_scheduler_job(scheduler.relay_module_job, config["module"]["relay_module"]["scheduler"])
    if scheduler.is_use_flag("module", "web_camera_module"):
        _create_scheduler_job(scheduler.web_camera_module_job, config["module"]["web_camera_module"]["scheduler"])

    while True:
        try:
            schedule.run_pending()
            sleep(1)
        except KeyboardInterrupt as e:
            scheduler.cleanup()
            raise e
        except Exception as e:
            logger.error(e)


def cleanup() -> None:
    """turn off power and cleanup function.
    """
    config = _full_load_config()

    scheduler = Scheduler(config)
    scheduler.turn_off_power()
    scheduler.cleanup()


def _full_load_config(config_path: str = "config.yaml") -> Dict:
    """Return full loaded config.

    Args:
        config_path:

    Returns:
        Config Dict
    """
    with open(config_path) as file:
        return yaml.full_load(file)


def _create_scheduler_job(callback_job: object, scheduler_config: Dict) -> None:
    """Create the scheduler job.

    Args:
        callback_job: user callback function
        scheduler_config: scheduler yaml config
    """
    if "interval_minutes" in scheduler_config:
        schedule.every(scheduler_config["interval_minutes"]).minutes.do(callback_job)
    elif "day_of_week" in scheduler_config:
        for day_of_week in scheduler_config["day_of_week"]:
            if "at_time" in scheduler_config:
                at_time_list = [scheduler_config["at_time"]] if isinstance(scheduler_config["at_time"], str) else scheduler_config["at_time"]
                for at_time in at_time_list:
                    getattr(schedule.every(), day_of_week).at(at_time).do(callback_job)
            else:
                getattr(schedule.every(), day_of_week).do(callback_job)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="main handler script")
    parser.add_argument("-f", "--function", type=str, default="main", help="set function name in this file")
    args = parser.parse_args()

    func_dict = {name: function for name, function in locals().items() if callable(function)}
    func_dict[args.function]()
