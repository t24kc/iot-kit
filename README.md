# iot-kitchen-garden
IoT kitchen garden system for using various sensors and Google Cloud services.


# Setup
## Install Packages
Install linux package.
```zsh
$ sudo apt-get update
$ sudo apt-get install python-opencv
```
Install python package.
```zsh
# install with poetry
$ poetry install

# install with pip
$ pip3 install -r requirements.txt
```

## Create Service Account
### By Website
Create a service account, and move the created service account file under `.gcp/service_account.json`.
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
$ gcloud iam service-accounts keys create .gcp/service_account.json --iam-account [Service Account Name]@[Project ID].iam.gserviceaccount.com
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
Create OAuth 2.0 Client ID with choosing `Desktop Application` type, and move the created client secrets file under `.gcp/client_secrets.json`.
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
Update config file `config.yaml` in advance.
- https://github.com/t24kc/iot-kitchen-garden/blob/main/config.yaml
```yaml
google:
  default:
    # service account path
    service_account_path: .gcp/service_account.json
    # client secrets path
    client_secrets_path: .gcp/client_secrets.json
  spread_sheet:
    use: True
    # spreadsheet id
    id: dummy # TODO update
  photo_library:
    use: True
    # photo library token path
    token_path: .gcp/photo_token.json
    # google photo album name
    album_title: IoT Kitchen Garden
    # save image directory
    img_dir: img
  mail:
    # mail token path
    token_path: .gcp/mail_token.json
    # email address to send
    to_address: dummy # TODO update
    summary:
      use: True
      subject: "[Summary] IoT Kitchen Garden"
      body: "Summary data of IoT sensor for the last week."
      scheduler:
        day_of_week: [ monday, tuesday, wednesday, thursday, friday, saturday, sunday ]
        at_time: "9:00:00"
    alert:
      use: True
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
    # time to turn on water (seconds)
    turn_on_time: 10
    scheduler:
      use: True
      day_of_week: [ monday, tuesday, wednesday, thursday, friday, saturday, sunday ]
      at_time: "8:30:00"
    conditions:
      use: True
      # time to skip the turning on relay module (minutes)
      skip_interval_minutes: 720
      # available filters.name [ light, temperature, humidity, co2, distance ]
      #   unit: light(lux), temperature(C), humidity(%), co2(ppm), distance(mm)
      # available filters.limit [ upper, lower ]
      filters:
        # example
        - name: light
          limit: upper
          threshold: 200
        - name: temperature
          limit: upper
          threshold: 35
  # web camera module
  web_camera_module:
    use: True
    scheduler:
      day_of_week: [ monday, tuesday, wednesday, thursday, friday, saturday, sunday ]
      at_time: "8:00:00"

sensor:
  scheduler:
    # time interval to monitor (minutes)
    interval_minutes: 10
  # light sensor
  bh1750fvi:
    use: True
  # temperature, humidity sensor
  sft31:
    use: True
  # co2, temperature, humidity sensor
  co2mini:
    use: True
  # distance, light sensor
  vl6180:
    use: True
```

Run script.
```zsh
# run with poetry
$ poetry run python handler.py

# run with system python
$ python3 handler.py
```

Cleanup script.
```zsh
# run with poetry
$ poetry run python handler.py -f cleanup

# run with system python
$ python3 handler.py -f cleanup
```