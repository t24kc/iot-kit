import os
import time
import re
import socket
import requests
from logging import getLogger, basicConfig, INFO
from typing import List, Dict, Optional, Any
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

logger = getLogger(__name__)
basicConfig(level=INFO)
logger.setLevel(INFO)

# Update scopes based on new requirements
SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
    "https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata",
    "https://www.googleapis.com/auth/photoslibrary.edit.appcreateddata"
]
MAX_API_RETRY = 3


class PhotoLibrary(object):
    def __init__(self, client_secrets_path: str, token_path: str) -> None:
        """PhotoLibrary Client Object.

        Args:
            client_secrets_path: OAuth 2.0 Client Secrets Path
            token_path: ID Token Path
        """
        self._client_secrets_path = client_secrets_path
        self._token_path = token_path

    def _get_service(self) -> Any:
        """Get photoslibrary.v1 Service.

        Assuming that it will be used in loop processing,
        create a service instance every time to avoid the access token expiration.

        Returns:
            A Resource object with photoslibrary.v1 service.
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
        service = build(
            "photoslibrary", "v1", credentials=credentials, static_discovery=False
        )

        return service

    @staticmethod
    def _execute_api(callback, *args, **kwargs) -> Any:
        """Execute photoslibrary.v1 service callback function.

        Args:
            callback: User callback function
            *args: args
            **kwargs: kwargs

        Returns:
            A callback result object with photoslibrary.v1 service.
        """
        for i in range(MAX_API_RETRY):
            try:
                return callback(*args, **kwargs)
            except Exception as e:
                logger.warning(e)
                if i < (MAX_API_RETRY - 1):
                    time.sleep(3)
        else:
            logger.error(f"{callback.__name__} retry out.")

    def create_album(self, album_title: str) -> str:
        """Create a new album.

        Args:
            album_title: New album title name

        Returns:
            A newly created album ID.
        """
        album = {"album": {"title": album_title}}
        response = self._execute_api(self._get_service().albums().create(body=album).execute)

        if "id" not in response:
            logger.error("Failed to create a new album.")
        logger.info(f"Succeeded to create a new album. id: {response['id']}, title: {response['title']}")

        return response["id"]

    def get_album_list(self) -> List:
        """Return all albums structure list.

        Returns:
            All albums structure list.
        """
        album_list = []
        page_token = None

        while True:
            response = self._execute_api(
                self._get_service().albums().list(pageSize=50, pageToken=page_token).execute
            )
            if "albums" not in response:
                break
            album_list.extend(response["albums"])
            if "nextPageToken" not in response:
                break
            page_token = response["nextPageToken"]

        return album_list

    def get_album(self, album_title: str) -> Optional[Dict]:
        """Get a target album.

        Args:
            album_title: album title

        Returns:
            An Album Resources dictionary.
        """
        album_list = self.get_album_list()
        for album in album_list:
            if album_title == album["title"]:
                return album

        return None

    def get_media_dict(self, album_id: str, filter_name: Optional[str] = None) -> Dict:
        """Return album media information dict.

        Args:
            album_id: Album ID
            filter_name: filter media name

        Returns:
            Album media information dict.
        """
        media_dict = {}
        page_token = None

        while True:
            search = {
                "albumId": album_id,
                "pageSize": 100,
                "pageToken": page_token
            }
            response = self._execute_api(
                self._get_service().mediaItems().search(body=search).execute,
            )
            if "mediaItems" not in response:
                break
            for media in response["mediaItems"]:
                file_name = media["filename"]
                if not filter_name or re.match(filter_name, file_name):
                    media_size = f"w{media['mediaMetadata']['width']}-h{media['mediaMetadata']['height']}"
                    media_dict[file_name] = {
                        "creation_time": media["mediaMetadata"]["creationTime"],
                        "base_url": f"{media['baseUrl']}={media_size}",
                        "product_url": media["productUrl"],
                    }
            if "nextPageToken" not in response:
                break
            page_token = response["nextPageToken"]

        return media_dict

    def upload_image(self, album_id: str, image_path: str) -> bool:
        """Upload images to album.

        Args:
            album_id: Album ID
            image_path: Image path to upload

        Returns:
            Returns whether the image could be uploaded.
        """
        if not os.path.isfile(image_path):
            logger.error("Image not exists.")
            return False

        # Use requests because python service api does not support.
        url = "https://photoslibrary.googleapis.com/v1/uploads"
        headers = {
            "Authorization": f"Bearer {self._get_service()._http.credentials.token}",
            "Content-Type": "application/octet-stream",
            "X-Goog-Upload-File-Name": os.path.basename(image_path),
            "X-Goog-Upload-Protocol": "raw",
        }

        with open(image_path, "rb") as image_data:
            response = self._execute_api(
                requests.post, url, data=image_data, headers=headers
            )
            if response.status_code != requests.codes.ok:
                logger.warning("Failed to upload image due to response status_code is not ok.")
                return False
            upload_token = response.content.decode("utf-8")

        new_media = {
            "albumId": album_id,
            "newMediaItems": [{"simpleMediaItem": {"uploadToken": upload_token}}],
        }
        response = self._execute_api(
            self._get_service().mediaItems().batchCreate(body=new_media).execute
        )
        if "newMediaItemResults" not in response:
            logger.warning("Failed to upload image due to newMediaItemResults key not exists.")
            return False

        status = response["newMediaItemResults"][0]["status"]
        logger.info(f"Succeeded upload of image to photo library. status: {status}")
        return True


def debug() -> None:
    """debug function.
    """
    import os, yaml
    from pathlib import Path

    parent_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    os.chdir(parent_dir)
    with open("config.yaml") as f:
        config = yaml.full_load(f)

    photo_library_client = PhotoLibrary(
        config["google"]["default"]["client_secrets_path"],
        config["google"]["photo_library"]["token_path"],
    )
    album_title = config["google"]["photo_library"]["album_title"]
    album = photo_library_client.get_album(album_title)
    if album:
        album_id = album["id"]
    else:
        album_id = photo_library_client.create_album(album_title)

    for image_path in Path(config["google"]["photo_library"]["img_dir"]).glob("?*.?*"):
        photo_library_client.upload_image(album_id, str(image_path))


if __name__ == "__main__":
    debug()
