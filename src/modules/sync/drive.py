import os
import io
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from src.utils.logger import get_logger

logger = get_logger("DriveSync")

SCOPES = ['https://www.googleapis.com/auth/drive.file']

class DriveSyncManager:
    def __init__(self, client_secret_file):
        self.client_secret_file = client_secret_file
        self.creds = None
        self.service = None
        self.token_file = os.path.join(os.getcwd(), 'data', 'token.json')

    def authenticate(self):
        try:
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.client_secret_file, SCOPES)
                    self.creds = flow.run_local_server(port=0)

                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())

            self.service = build('drive', 'v3', credentials=self.creds)
            logger.info("Successfully authenticated with Google Drive.")
            return True
        except Exception as e:
            logger.error(f"Google Drive auth failed: {e}")
            return False

    def upload_file(self, file_path, folder_id=None):
        if not self.service:
            logger.error("Drive service not authenticated.")
            return None

        try:
            file_metadata = {'name': os.path.basename(file_path)}
            if folder_id:
                file_metadata['parents'] = [folder_id]

            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            logger.info(f"File uploaded successfully. File ID: {file.get('id')}")
            return file.get('id')
        except Exception as e:
            logger.error(f"Failed to upload file to Drive: {e}")
            return None

    def download_file(self, file_id, destination_path):
        if not self.service:
            logger.error("Drive service not authenticated.")
            return False

        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = io.FileIO(destination_path, 'wb')
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            logger.info(f"File downloaded successfully to {destination_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download file from Drive: {e}")
            return False
