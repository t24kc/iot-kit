# sensor
Sensor and Module Client Objects.

# Usage
## BH1750FVI
Digital light sensor script.
```zsh
$ python3 BH1750FVI.py --help
usage: BH1750FVI.py [-h] [-i INTERVAL]

Digital Light Sensor Script

optional arguments:
  -h, --help            show this help message and exit
  -i INTERVAL, --interval INTERVAL
                        set script interval seconds
```

## CO2MINI
CO2 sensor script.
```zsh
$ python3 CO2MINI.py --help
usage: CO2MINI.py [-h] [-i INTERVAL]

CO2 Sensor Script

optional arguments:
  -h, --help            show this help message and exit
  -i INTERVAL, --interval INTERVAL
                        set script interval seconds
```

## SHT31
Temperature and humidity sensor script.
```zsh
$ python3 SHT31.py --help
usage: SHT31.py [-h] [-i INTERVAL]

Temperature and Humidity Sensor Script

optional arguments:
  -h, --help            show this help message and exit
  -i INTERVAL, --interval INTERVAL
                        set script interval seconds
```

## VL6180
Infrared distance sensor script.
```zsh
$ python3 VL6180.py --help
usage: VL6180.py [-h] [-i INTERVAL]

Infrared Distance Sensor Script

optional arguments:
  -h, --help            show this help message and exit
  -i INTERVAL, --interval INTERVAL
                        set script interval seconds
```

## RelayModule
Relay module script.
```zsh
$ python3 relay_module.py --help
usage: relay_module.py [-h] [-i INTERVAL]

Relay module script

optional arguments:
  -h, --help            show this help message and exit
  -i INTERVAL, --interval INTERVAL
                        set relay module turn on seconds
```

## WebCameraModule
Web camera module script.
```zsh
$ python3 web_camera_module.py --help
usage: web_camera_module.py [-h] [--fourcc FOURCC] [--width WIDTH]
                            [--height HEIGHT] [--fps FPS] [--focus FOCUS]

Web camera module script

optional arguments:
  -h, --help       show this help message and exit
  --fourcc FOURCC  set video capture frame fourcc (MJPG, YUYV, H264, etc)
  --width WIDTH    set video capture frame width (1280, 1920, 3840, etc)
  --height HEIGHT  set video capture frame height (720, 1080, 2160, etc)
  --fps FPS        set video capture frame fps (15, 30, 60, etc)
  --focus FOCUS    set video capture frame focus (0 ~ 255)
```
