# iot-kit
![raspberry pi model](https://img.shields.io/badge/Raspberry%20Pi%20Model-3B%2B%20%7C%204B-red)
![python](https://img.shields.io/badge/python-3.7-blue)
![release](https://img.shields.io/github/v/release/t24kc/iot-kit)

IoT kitchen garden system for using various sensors and Google Cloud services.


# Setup
## Install Packages
Install linux package.
```zsh
$ sudo apt update
$ sudo apt install libatlas-base-dev
```
Install python package.
```zsh
# install with pip
$ pip3 install -r requirements.txt
# install with poetry (optional)
$ poetry install
```

## Create Service Account
### By Website
Create a service account, and move the created service account file under `gcp/service_account.json`.
- https://cloud.google.com/iam/docs/creating-managing-service-accounts
### By command line
```zsh
# login google suite
$ gcloud auth login
# create GCP project
$ gcloud projects create [Project ID]
# create service account
$ gcloud iam service-accounts create [Service Account Name] --display-name [Display Name]
# generate service account key
$ gcloud iam service-accounts keys create gcp/service_account.json --iam-account [Service Account Name]@[Project ID].iam.gserviceaccount.com
```

## Enable APIs
### By Website
Enable the `Google Sheets API` and `Photos Library API` and `Gmail API`.
- https://cloud.google.com/apis/docs/getting-started#enabling_apis
- https://console.cloud.google.com/apis/library
### By command line
```zsh
# enable google sheets api, photos library api, gmail api
$ gcloud services enable sheets.googleapis.com photoslibrary.googleapis.com gmail.googleapis.com
```

## Create OAuth 2.0 Client ID
Create OAuth 2.0 Client ID with choosing `Desktop Application` type, and move the created client secrets file under `gcp/client_secrets.json`.
- https://developers.google.com/workspace/guides/create-credentials#desktop-app
- https://console.cloud.google.com/apis/credentials

## Update Credential Consent
Create OAuth consent screen for requesting access data.
- https://support.google.com/cloud/answer/6158849
- https://console.cloud.google.com/apis/credentials/consent

## Add Sheet Permission
Create a GoogleSpreadSheet and from "Share" add the edit permission of the service account created above.

## Add CO2-mini USB Device Permission
If you don't want to run your script as root make sure you have sufficient rights to access the device file.
Save it as `/etc/udev/rules.d/90-co2mini.rules` and add the script user to the group `plugdev`.
```zsh
ACTION=="remove", GOTO="co2mini_end"
SUBSYSTEMS=="usb", KERNEL=="hidraw*", ATTRS{idVendor}=="04d9", ATTRS{idProduct}=="a052", GROUP="plugdev", MODE="0660", SYMLINK+="co2mini%n", GOTO="co2mini_end"
LABEL="co2mini_end"
```

# Usage
## Update config
Update config file `config.yaml` in advance. Change unused sensors and modules to `use: False`.
- https://github.com/t24kc/iot-kit/blob/main/config.yaml
```yaml
google:
  default:
    # service account path
    service_account_path: gcp/service_account.json
    # client secrets path
    client_secrets_path: gcp/client_secrets.json
  spread_sheet:
    use: True # or False
    # spreadsheet id
    id: dummy # TODO update
  photo_library:
    use: True # or False
    # photo library token path
    token_path: gcp/photo_token.json
    # google photo album name
    album_title: IoT Kitchen Garden
    # save image directory
    img_dir: img
  mail:
    # mail token path
    token_path: gcp/mail_token.json
    # email address to send
    to_address: dummy # TODO update
    summary:
      use: True # or False
      subject: "[Summary] IoT Kitchen Garden"
      body: "Summary data of IoT sensor for the last {from_days} days."
      from_days: 7
      scheduler:
        day_of_week: [ monday, tuesday, wednesday, thursday, friday, saturday, sunday ]
        at_time: ["09:00:00"]
    alert:
      use: True # or False
      subject: "[Alert] IoT Kitchen Garden"
      body:
        # {name}, {threshold}, {value}, {unit} will be converted
        upper: "{name} has risen above the setting value of {threshold}{unit} (currently: {value}{unit})."
        lower: "{name} has dropped below the setting value of {threshold}{unit} (currently: {value}{unit})."
      # time to skip the same type of notification (minutes)
      skip_interval_minutes: 120
      # available filters.name [ light, temperature, humidity, co2, distance ]
      #   unit: light(lux), temperature(C), humidity(%), co2(ppm), distance(mm)
      # available filters.limit [ upper, lower ]
      filters:
        # example
        - name: temperature
          limit: upper
          threshold: 35
        - name: temperature
          limit: lower
          threshold: 0
        - name: co2
          limit: upper
          threshold: 1500
        - name: co2
          limit: lower
          threshold: 300

module:
  # relay module
  relay_module:
    # time to turn on power (minutes)
    turn_on_minutes: 0.5
    scheduler:
      use: True # or False
      day_of_week: [ monday, tuesday, wednesday, thursday, friday, saturday, sunday ]
      at_time: ["08:30:00"]
    conditions:
      use: True # or False
      # time to skip the turning on relay module (minutes)
      skip_interval_minutes: 720
      # available filters.name [ light, temperature, humidity, co2, distance ]
      #   unit: light(lux), temperature(C), humidity(%), co2(ppm), distance(mm)
      # available filters.limit [ upper, lower ]
      filters:
        # example
        - name: light
          limit: upper
          threshold: 100000
        - name: temperature
          limit: upper
          threshold: 35
  # web camera module
  web_camera_module:
    use: True # or False
    scheduler:
      day_of_week: [ monday, tuesday, wednesday, thursday, friday, saturday, sunday ]
      at_time: ["08:00:00"]
    # video capture frame settings
    settings:
      width: 1280
      height: 960
      fourcc: null # MJPG, YUYV, H264, etc
      fps: null # 15, 30, 60, etc
      focus: null # 0 ~ 255

sensor:
  scheduler:
    # time interval to monitor (minutes)
    interval_minutes: 10
  # light sensor
  bh1750fvi:
    use: True # or False
  # temperature, humidity sensor
  sht31:
    use: True # or False
  # co2, temperature, humidity sensor
  co2mini:
    use: True # or False
    decrypt: False # or True
  # distance, light sensor
  vl6180:
    use: True # or False
```

## Run Script
script usage.
- https://t24kc.github.io/iot-kit/handler.html
```zsh
$ python3 handler.py --help
usage: handler.py [-h] [-f FUNCTION]

main handler script

optional arguments:
  -h, --help            show this help message and exit
  -f FUNCTION, --function FUNCTION
                        set function name in this file
```

main scheduler script.
```zsh
# run with system python
$ python3 handler.py
# run with poetry (optional)
$ poetry run python handler.py
```

cleanup script.
```zsh
# run with system python
$ python3 handler.py -f cleanup
# run with poetry (optional)
$ poetry run python handler.py -f cleanup
```
