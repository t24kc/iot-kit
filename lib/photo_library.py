import os
import time
import requests
from logging import getLogger, INFO
from typing import List, Set, Any, Optional, Dict
from httplib2 import Http
from oauth2client import file, client, tools
from googleapiclient.discovery import build

logger = getLogger(__name__)
logger.setLevel(INFO)

SCOPES = ["https://www.googleapis.com/auth/photoslibrary"]
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
        self._flags = tools.argparser.parse_args()
        self._flags.noauth_local_webserver = True

    def _get_service(self) -> Any:
        """Get photoslibrary.v1 Service.

        Assuming that it will be used in loop processing,
        create a service instance every time to avoid the access token expiration.

        Returns:
            A Resource object with photoslibrary.v1 service.
        """
        store = file.Storage(self._token_path)
        token = store.get()
        if not token or token.invalid:
            flow = client.flow_from_clientsecrets(self._client_secrets_path, SCOPES)
            token = tools.run_flow(flow, store, self._flags)
        service = build(
            "photoslibrary", "v1", http=token.authorize(Http()), static_discovery=False
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

    def get_media_set(self, album_id: str, filter_name: Optional[str] = None) -> Set:
        """Return all album medias name set.

        Args:
            album_id: Album ID
            filter_name: filter media name

        Returns:
            All album medias name set.
        """
        media_set = set()
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
                if not filter_name or filter_name in file_name:
                    media_set.add(file_name)
            if "nextPageToken" not in response:
                break
            page_token = response["nextPageToken"]

        return media_set

    def upload_image(self, album_id: str, image_path: str) -> bool:
        """Upload images to album.

        Args:
            album_id: Album ID
            image_path: Image path to upload

        Returns:
            Returns whether the image could be uploaded.
        """
        # Use requests because python service api does not support.
        url = "https://photoslibrary.googleapis.com/v1/uploads"
        headers = {
            "Authorization": f"Bearer {self._get_service()._http.request.credentials.access_token}",
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
