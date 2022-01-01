import time
import gspread
from logging import getLogger, INFO
from typing import List, Dict, Any
from oauth2client.service_account import ServiceAccountCredentials

logger = getLogger(__name__)
logger.setLevel(INFO)

SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
DEFAULT_SHEET_INDEX = 0
MAX_API_RETRY = 3


class SpreadSheet(object):
    def __init__(self, service_account_path: str, spread_sheet_key: str) -> None:
        """SpreadSheet Client Object.

        Args:
            service_account_path:
            spread_sheet_key:
        """
        self._service_account_path = service_account_path
        self._spread_sheet_key = spread_sheet_key

    def _get_service(self) -> Any:
        """Google spreadsheet Service Object.

        Assuming that it will be used in loop processing,
        create a service instance every time to avoid the access token expiration.

        Returns:
            A Resource object with Google spreadsheet service.
        """
        credentials = ServiceAccountCredentials.from_json_keyfile_name(
            self._service_account_path, SCOPES
        )
        return gspread.authorize(credentials).open_by_key(self._spread_sheet_key)

    @staticmethod
    def _execute_api(callback, *args) -> Any:
        """Execute Google spreadsheet service callback function.

        Args:
            callback: User callback function
            *args: args

        Returns:
            A callback result object with Google spreadsheet service.
        """
        for i in range(MAX_API_RETRY):
            try:
                return callback(*args)
            except Exception as e:
                logger.warning(e)
                if i < (MAX_API_RETRY - 1):
                    time.sleep(3)
        else:
            logger.error(f"{callback.__name__} retry out.")

    def get_label_value(self, label: str, index: int = DEFAULT_SHEET_INDEX) -> str:
        """Get Google spreadsheet label value.

        Args:
            label: Google spreadsheet label. (ex) "A1"
            index: Google spreadsheet tab index. (ex) 0

        Returns:
            Google spreadsheet label value.
        """
        return self._execute_api(
            self._get_service().get_worksheet(index).acell, label
        ).value

    def set_label_value(
        self, label: str, value: str, index: int = DEFAULT_SHEET_INDEX
    ) -> Dict:
        """Set Google spreadsheet label value.

        Args:
            label: Google spreadsheet label. (ex) "A1"
            value: Input value
            index: Google spreadsheet tab index. (ex) 0

        Returns:
            Google spreadsheet input response message.
        """
        return self._execute_api(
            self._get_service().get_worksheet(index).update_acell, label, value
        )

    def row_values(self, row: int, index: int = DEFAULT_SHEET_INDEX) -> List:
        """Get Google spreadsheet all row values.

        Args:
            row: Google spreadsheet row. (ex) 1
            index: Google spreadsheet tab index. (ex) 0

        Returns:
            Google spreadsheet all row values.
        """
        assert row > 0, "Row must be at least 1"
        return self._execute_api(
            self._get_service().get_worksheet(index).row_values, row
        )

    def col_values(self, col: int, index: int = DEFAULT_SHEET_INDEX) -> List:
        """Get Google spreadsheet all column values.

        Args:
            col: Google spreadsheet column. (ex) 1
            index: Google spreadsheet tab index. (ex) 0

        Returns:
            Google spreadsheet all column values.
        """
        assert col > 0, "Column must be at least 1"
        return self._execute_api(
            self._get_service().get_worksheet(index).col_values, col
        )

    def get_all_values(self, index: int = DEFAULT_SHEET_INDEX) -> List:
        """Get Google spreadsheet all sheet values.

        Args:
            index: Google spreadsheet tab index. (ex) 0

        Returns:
            Google spreadsheet all sheet values.
        """
        return self._execute_api(
            self._get_service().get_worksheet(index).get_all_values
        )

    def append_row(self, values: List, index: int = DEFAULT_SHEET_INDEX) -> Dict:
        """Append Google spreadsheet row at the end.

        Args:
            values: Input values list
            index: Google spreadsheet tab index. (ex) 0

        Returns:
            Google spreadsheet input response message.
        """
        response = self._execute_api(
            self._get_service().get_worksheet(index).append_row, values
        )
        logger.info(f"Appended a row to the spreadsheet of {values}.")
        return response

    def clear(self, index: int = DEFAULT_SHEET_INDEX) -> Dict:
        """Clear Google spreadsheet all rows at once.

        Args:
            index: Google spreadsheet tab index. (ex) 0

        Returns:
            Google spreadsheet clear response message.
        """
        response = self._execute_api(
            self._get_service().get_worksheet(index).clear
        )
        logger.info("Cleared all rows in the spreadsheet.")
        return response
