# lib
Google Service Client Objects.

# Usage
## Mail
Google Mail Script.
- https://t24kc.github.io/iot-kit/lib.html#module-lib.mail
```zsh
$ python3 mail.py --help
usage: mail.py [-h] [-a TO_ADDRESS] [-s SUBJECT] [-b BODY]

Google Mail Script

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        set send mail address (default dummy)
  -s SUBJECT, --subject SUBJECT
                        set send mail subject (default test subject)
  -b BODY, --body BODY  set send mail body (default test body)

```

## PhotoLibrary
Google Photo Library Script.
- https://t24kc.github.io/iot-kit/lib.html#module-lib.photo_library
```zsh
$ python3 photo_library.py
usage: photo_library.py

Google Photo Library Script
  Upload images from the img folder to Google PhotoLibrary
```

## SpreadSheet
Google Spread Sheet Script.
- https://t24kc.github.io/iot-kit/lib.html#module-lib.spread_sheet
```zsh
$ python3 spread_sheet.py --help
usage: spread_sheet.py [-h] [-s SPREAD_SHEET_ID] [-t INPUT_TEXT]

Google Spread Sheet Script

optional arguments:
  -h, --help            show this help message and exit
  -s SPREAD_SHEET_ID, --spread-sheet-id SPREAD_SHEET_ID
                        set spread sheet id (default dummy)
  -t INPUT_TEXT, --input-text INPUT_TEXT
                        set spread sheet input text (default test)
```
