import os
import socket
import time
import base64
import mimetypes
from logging import getLogger, basicConfig, INFO
from typing import Dict, List, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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

    def _get_service(self) -> Any:
        """gmail.v1 Service Object.

        Assuming that it will be used in loop processing,
        create a service instance every time to avoid the access token expiration.

        Returns:
            A Resource object with gmail.v1 service.
        """
        credentials = None
        if os.path.exists(self._token_path):
            credentials = Credentials.from_authorized_user_file(self._token_path, SCOPES)

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self._client_secrets_path, SCOPES)
                credentials = flow.run_local_server(port=0, open_browser=False)
            with open(self._token_path, "w") as token:
                token.write(credentials.to_json())

        socket.setdefaulttimeout(300)
        service = build("gmail", "v1", credentials=credentials)

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
        to: str, subject: str, body: str, file_path_list: List[str]
    ) -> Dict:
        """Create email message with image.

        Args:
            to: email message to
            subject: email message subject
            body: email message body
            file_path_list: email image file path list

        Returns:
            A raw data for email.mime.multipart decode dict.
        """
        message = MIMEMultipart()
        message["to"] = to
        message["from"] = "me"
        message["subject"] = subject

        msg = MIMEText(body)
        message.attach(msg)

        content_type, encoding = mimetypes.guess_type(file_path_list[0])
        if content_type is None or encoding is not None:
            content_type = "application/octet-stream"
        main_type, sub_type = content_type.split("/", 1)
        assert main_type == "image", "type is not image"

        for file_path in file_path_list:
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


def debug() -> None:
    """debug function.
    """
    import argparse, os, yaml

    parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.chdir(parent_dir)
    with open("config.yaml") as f:
        config = yaml.full_load(f)

    default_subject = "test subject"
    default_body = "test body"
    parser = argparse.ArgumentParser(description="Google Mail Script")
    parser.add_argument(
        "-a", "--address", type=str, default=config["google"]["mail"]["to_address"],
        help=f"set send mail address (default {config['google']['mail']['to_address']})",
    )
    parser.add_argument(
        "-s", "--subject", type=str, default=default_subject,
        help=f"set send mail subject (default {default_subject})",
    )
    parser.add_argument(
        "-b", "--body", type=str, default=default_body,
        help=f"set send mail body (default {default_body})",
    )
    args = parser.parse_args()

    mail_client = Mail(
        config["google"]["default"]["client_secrets_path"],
        config["google"]["mail"]["token_path"],
    )
    message = mail_client.create_message(args.address, args.subject, args.body)
    mail_client.send_message(message)
    logger.info(args.body)


if __name__ == "__main__":
    debug()
