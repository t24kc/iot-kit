import os
import time
import base64
import mimetypes
from logging import getLogger, basicConfig, INFO
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from httplib2 import Http
from oauth2client import file, client, tools
from googleapiclient.discovery import build

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
MAX_API_RETRY = 3


class Mail(object):
    def __init__(self, client_secrets_path: str, token_path: str) -> None:
        """Mail Client Object.

        Args:
            client_secrets_path: OAuth 2.0 Client Secrets Path
            token_path: ID Token Path
        """
        self._client_secrets_path = client_secrets_path
        self._token_path = token_path
        self._flags = tools.argparser.parse_args()
        self._flags.noauth_local_webserver = True

    def _get_service(self) -> Any:
        """gmail.v1 Service Object.

        Assuming that it will be used in loop processing,
        create a service instance every time to avoid the access token expiration.

        Returns:
            A Resource object with gmail.v1 service.
        """
        store = file.Storage(self._token_path)
        token = store.get()
        if not token or token.invalid:
            flow = client.flow_from_clientsecrets(self._client_secrets_path, SCOPES)
            token = tools.run_flow(flow, store, self._flags)
        service = build("gmail", "v1", http=token.authorize(Http()))

        return service

    @staticmethod
    def _execute_api(callback) -> Any:
        """Execute gmail.v1 service callback function.

        Args:
            callback: User callback function

        Returns:
            A callback result object with gmail.v1 service.
        """
        for i in range(MAX_API_RETRY):
            try:
                return callback.execute()
            except Exception as e:
                logger.warning(e)
                if i < (MAX_API_RETRY - 1):
                    time.sleep(3)
        else:
            logger.error(f"{callback.methodId} retry out.")

    @staticmethod
    def create_message(to: str, subject: str, body: str) -> Dict:
        """Create email message.

        Args:
            to: email message to
            subject: email message subject
            body: email message body

        Returns:
            A raw data for email.mime.text decode dict.
        """
        message = MIMEText(body)
        message["to"] = to
        message["from"] = "me"
        message["subject"] = subject

        byte_msg = message.as_string().encode()
        return {"raw": base64.urlsafe_b64encode(byte_msg).decode()}

    @staticmethod
    def create_message_with_image(
        to: str, subject: str, body: str, file_path: str
    ) -> Dict:
        """Create email message with image.

        Args:
            to: email message to
            subject: email message subject
            body: email message body
            file_path: email image file path

        Returns:
            A raw data for email.mime.multipart decode dict.
        """
        message = MIMEMultipart()
        message["to"] = to
        message["from"] = "me"
        message["subject"] = subject

        msg = MIMEText(body)
        message.attach(msg)

        content_type, encoding = mimetypes.guess_type(file_path)
        if content_type is None or encoding is not None:
            content_type = "application/octet-stream"
        main_type, sub_type = content_type.split("/", 1)
        assert main_type == "image", "type is not image"

        with open(file_path, "rb") as fp:
            msg = MIMEImage(fp.read(), _subtype=sub_type)

        msg.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(file_path)
        )
        message.attach(msg)

        byte_msg = message.as_string().encode()
        return {"raw": base64.urlsafe_b64encode(byte_msg).decode()}

    def send_message(self, body: Dict) -> Dict:
        """Send email message.

        Args:
            body: email message body

        Returns:
            Google email send response message.
        """
        return self._execute_api(
            self._get_service().users().messages().send(userId="me", body=body)
        )
