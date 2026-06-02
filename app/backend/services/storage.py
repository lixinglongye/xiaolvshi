import logging
import hashlib
import hmac
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Optional, Union
from urllib.parse import urlencode, urljoin

import httpx
from core.config import settings
from schemas.storage import (
    BucketInfo,
    BucketListResponse,
    BucketRequest,
    BucketResponse,
    DeleteResponse,
    FileUpDownRequest,
    FileUpDownResponse,
    ObjectInfo,
    ObjectListResponse,
    ObjectRequest,
    OSSBaseModel,
    RenameRequest,
    RenameResponse,
)

logger = logging.getLogger(__name__)


class StorageService:
    """Service for handling file upload and display with ObjectStorage service integration."""

    def __init__(self):
        self.oss_service_url = getattr(settings, "oss_service_url", None)
        self.oss_api_key = getattr(settings, "oss_api_key", None)
        self.local_mode = not (self.oss_service_url and self.oss_api_key)
        self.local_storage_dir = Path(
            getattr(settings, "local_storage_dir", Path(__file__).resolve().parents[1] / "local_storage")
        )
        if self.local_mode:
            self.local_storage_dir.mkdir(parents=True, exist_ok=True)
            self.headers = {}
            return

        self.headers = {
            "Authorization": f"Bearer {self.oss_api_key}",
            "Content-Type": "application/json",
        }

    async def create_bucket(self, request: BucketRequest) -> BucketResponse:
        """
        Create a bucket name
        """
        if self.local_mode:
            self._local_bucket_path(request.bucket_name).mkdir(parents=True, exist_ok=True)
            return BucketResponse(
                bucket_name=request.bucket_name,
                visibility=request.visibility,
                created_at=datetime.now().isoformat(),
            )

        endpoint = "api/v1/infra/client/oss/buckets"
        payload = {"bucket_name": request.bucket_name, "visibility": request.visibility}
        try:
            result = await self._apost_oss_service(endpoint, payload)
            return BucketResponse(bucket_name=result.get("bucket_name"), created_at=result.get("created_at"))
        except Exception as e:
            logger.error(f"Failed to create bucket: {e}")
            raise

    async def list_buckets(self) -> BucketListResponse:
        """
        List buckets of the user
        """
        if self.local_mode:
            list_buckets = BucketListResponse()
            paths = self.local_storage_dir.iterdir() if self.local_storage_dir.exists() else []
            for path in sorted(paths):
                if path.is_dir():
                    list_buckets.buckets.append(BucketInfo(bucket_name=path.name, visibility="private"))
            return list_buckets

        endpoint = "api/v1/infra/client/oss/buckets"
        try:
            result = await self._aget_oss_service(endpoint=endpoint, params={})
            list_buckets = BucketListResponse()
            for item in result["buckets"]:
                list_buckets.buckets.append(BucketInfo(bucket_name=item["bucket_name"], visibility=item["visibility"]))
            return list_buckets
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            raise

    async def list_objects(self, request: OSSBaseModel) -> ObjectListResponse:
        """
        List objests from the bucket
        """
        if self.local_mode:
            list_objs = ObjectListResponse()
            bucket_path = self._local_bucket_path(request.bucket_name)
            paths = bucket_path.iterdir() if bucket_path.exists() else []
            for path in sorted(paths):
                if path.is_file():
                    list_objs.objects.append(
                        ObjectInfo(
                            bucket_name=request.bucket_name,
                            object_key=path.name,
                            size=path.stat().st_size,
                            last_modified=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                            etag=self._file_etag(path),
                        )
                    )
            return list_objs

        endpoint = f"api/v1/infra/client/oss/buckets/{request.bucket_name}/objects"
        try:
            result = await self._aget_oss_service(endpoint=endpoint, params={})
            list_objs = ObjectListResponse()
            for item in result["objects"]:
                list_objs.objects.append(
                    ObjectInfo(
                        bucket_name=request.bucket_name,
                        object_key=item["key"],
                        size=item["size"],
                        last_modified=item["last_modified"],
                        etag=item["etag"],
                    )
                )
            return list_objs
        except Exception as e:
            logger.error(f"Failed to list bucket objects: {e}")
            raise

    async def get_object_info(self, request: ObjectRequest) -> ObjectInfo:
        """
        Get object metadata from the bucket
        """
        if self.local_mode:
            path = self._local_object_path(request.bucket_name, request.object_key)
            if not path.exists():
                raise ValueError("Object not found in local storage")
            return ObjectInfo(
                bucket_name=request.bucket_name,
                object_key=request.object_key,
                size=path.stat().st_size,
                last_modified=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                etag=self._file_etag(path),
            )

        try:
            endpoint = f"api/v1/infra/client/oss/buckets/{request.bucket_name}/objects/metadata"
            params = {"object_key": request.object_key}
            result = await self._aget_oss_service(endpoint, params)
            return ObjectInfo(
                bucket_name=request.bucket_name,
                object_key=result["key"],
                size=result["size"],
                last_modified=result["last_modified"],
                etag=result["etag"],
            )
        except Exception as e:
            logger.error(f"Failed to get object metadata: {e}")
            raise

    async def rename_object(self, request: RenameRequest) -> dict:
        if self.local_mode:
            source = self._local_object_path(request.bucket_name, request.source_key)
            target = self._local_object_path(request.bucket_name, request.target_key)
            if not source.exists():
                raise ValueError("Source object not found in local storage")
            if target.exists() and not request.overwrite_key:
                raise ValueError("Target object already exists")
            target.parent.mkdir(parents=True, exist_ok=True)
            source.replace(target)
            return RenameResponse(success=True)

        endpoint = f"api/v1/infra/client/oss/buckets/{request.bucket_name}/objects/rename"
        payload = {
            "overwrite_key": request.overwrite_key,
            "source_key": request.source_key,
            "target_key": request.target_key,
        }
        try:
            await self._apost_oss_service(endpoint, payload)
            return RenameResponse(success=True)
        except Exception as e:
            logger.error(f"Failed to rename object: {e}")
            raise

    async def delete_object(self, request: ObjectRequest) -> DeleteResponse:
        if self.local_mode:
            path = self._local_object_path(request.bucket_name, request.object_key)
            if path.exists():
                path.unlink()
            return DeleteResponse(success=True)

        endpoint = f"api/v1/infra/client/oss/buckets/{request.bucket_name}/objects"
        payload = {"object_keys": [request.object_key]}
        try:
            await self._adelete_oss_service(endpoint, payload)
            return DeleteResponse(success=True)
        except Exception as e:
            logger.error(f"Failed to rename object: {e}")
            raise

    async def create_upload_url(self, request: FileUpDownRequest) -> FileUpDownResponse:
        """
        Create presigned URL for file upload with access URL.
        """
        if self.local_mode:
            token = self.create_local_token(request.bucket_name, request.object_key)
            expires_at = (datetime.now() + timedelta(hours=12)).isoformat()
            query = urlencode(
                {
                    "bucket_name": request.bucket_name,
                    "object_key": request.object_key,
                    "token": token,
                }
            )
            return FileUpDownResponse(
                upload_url=f"{settings.backend_url}/api/v1/storage/local-upload?{query}",
                expires_at=expires_at,
            )

        endpoint = f"/api/v1/infra/client/oss/buckets/{request.bucket_name}/objects/upload_url"
        payload = {"expires_in": 0, "object_key": request.object_key}
        try:
            result = await self._apost_oss_service(endpoint, payload)
            # Format response according to ObjectStorage service response
            return FileUpDownResponse(
                upload_url=result.get("upload_url"),
                expires_at=result.get("expires_at"),
            )
        except Exception as e:
            logger.error(f"Failed to create upload URL: {e}")
            raise

    async def create_download_url(self, request: FileUpDownRequest) -> FileUpDownResponse:
        """
        Create presigned URL for file download with access URL.
        """
        if self.local_mode:
            path = self._local_object_path(request.bucket_name, request.object_key)
            if not path.exists():
                raise ValueError("Object not found in local storage")
            token = self.create_local_token(request.bucket_name, request.object_key)
            expires_at = (datetime.now() + timedelta(hours=12)).isoformat()
            query = urlencode(
                {
                    "bucket_name": request.bucket_name,
                    "object_key": request.object_key,
                    "token": token,
                }
            )
            return FileUpDownResponse(
                download_url=f"{settings.backend_url}/api/v1/storage/local-download?{query}",
                expires_at=expires_at,
            )

        endpoint = f"/api/v1/infra/client/oss/buckets/{request.bucket_name}/objects/download_url"
        content_type, _ = mimetypes.guess_type(str(request.object_key))
        if not content_type:
            content_type = "application/octet-stream"
        payload = {
            "content_type": content_type,  # like "image/jpeg"
            "expires_in": 0,
            "object_key": request.object_key,
        }
        try:
            result = await self._apost_oss_service(endpoint, payload)
            # Format response according to ObjectStorage service response
            return FileUpDownResponse(
                download_url=result.get("download_url"),
                expires_at=result.get("expires_at"),
            )

        except Exception as e:
            logger.error(f"Failed to create upload URL: {e}")
            raise

    async def download_object_bytes(self, request: FileUpDownRequest) -> bytes:
        """Download an object through a short-lived presigned URL."""
        if self.local_mode:
            path = self._local_object_path(request.bucket_name, request.object_key)
            if not path.exists():
                raise ValueError("Object not found in local storage")
            return path.read_bytes()

        download_info = await self.create_download_url(request)
        if not download_info.download_url:
            raise ValueError("ObjectStorage service did not return a download URL.")

        try:
            async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
                response = await client.get(download_info.download_url)
                response.raise_for_status()
                return response.content
        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to download object: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except Exception as e:
            logger.error(f"Failed to download object: {e}")
            raise

    def create_local_token(self, bucket_name: str, object_key: str) -> str:
        payload = f"{bucket_name}:{object_key}".encode("utf-8")
        secret = str(settings.jwt_secret_key).encode("utf-8")
        return hmac.new(secret, payload, hashlib.sha256).hexdigest()

    def verify_local_token(self, bucket_name: str, object_key: str, token: str) -> bool:
        expected = self.create_local_token(bucket_name, object_key)
        return hmac.compare_digest(expected, token or "")

    async def save_local_upload(self, request: FileUpDownRequest, token: str, data: bytes) -> ObjectInfo:
        if not self.verify_local_token(request.bucket_name, request.object_key, token):
            raise ValueError("Invalid local upload token")
        if not data:
            raise ValueError("Uploaded file is empty")

        bucket_path = self._local_bucket_path(request.bucket_name)
        bucket_path.mkdir(parents=True, exist_ok=True)
        path = self._local_object_path(request.bucket_name, request.object_key)
        path.write_bytes(data)
        return ObjectInfo(
            bucket_name=request.bucket_name,
            object_key=request.object_key,
            size=path.stat().st_size,
            last_modified=datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            etag=self._file_etag(path),
        )

    def resolve_local_download(self, request: FileUpDownRequest, token: str) -> Path:
        if not self.verify_local_token(request.bucket_name, request.object_key, token):
            raise ValueError("Invalid local download token")
        path = self._local_object_path(request.bucket_name, request.object_key)
        if not path.exists():
            raise ValueError("Object not found in local storage")
        return path

    def _local_bucket_path(self, bucket_name: str) -> Path:
        return self.local_storage_dir / bucket_name

    def _local_object_path(self, bucket_name: str, object_key: str) -> Path:
        base_name = Path(object_key).name
        return self._local_bucket_path(bucket_name) / base_name

    def _file_etag(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    async def _aget_oss_service(self, endpoint: str, params: dict) -> dict:
        return await self._arequest_oss_service("GET", endpoint, params=params)

    async def _apost_oss_service(self, endpoint: str, payload: dict) -> Union[dict, list]:
        return await self._arequest_oss_service("POST", endpoint, payload=payload)

    async def _adelete_oss_service(self, endpoint: str, payload: dict) -> Union[dict, list]:
        return await self._arequest_oss_service("DELETE", endpoint, payload=payload)

    async def _arequest_oss_service(
        self,
        method: Literal["GET", "POST", "DELETE"],
        endpoint: str,
        params: Optional[dict] = None,
        payload: Optional[dict] = None,
    ) -> Union[dict, list]:
        """统一的 OSS 服务请求方法"""
        url = urljoin(self.oss_service_url, endpoint)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=payload,
                )
                response.raise_for_status()
                result = response.json()

                if result.get("code") != 0:
                    logger.warning(f"ObjectStorage service error: {result}")
                    error_msg = result.get("error", "Unknown error")
                    message = result.get("message", "")
                    raise ValueError(f"ObjectStorage service error: {error_msg}. {message}")

                return result.get("data", [])
        except httpx.HTTPStatusError as e:
            error_msg = f"ObjectStorage service HTTP error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"Failed to call ObjectStorage service: {e}")
            raise
