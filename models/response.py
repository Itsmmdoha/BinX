from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

from database.db import Base
from .shared import Visibility

class VaultInfoModel(BaseModel):
    vault: str
    date_created: datetime
    size: int
    used_storage: int

    class Config:
        orm_mode = True

class FileInfo(BaseModel):
    file: str
    visibility: Visibility
    id: UUID 
    size: int
    date_created: datetime

    class Config:
        orm_mode = True

class VaultModel(BaseModel):  # renamed to match PascalCase convention
    vault: VaultInfoModel
    files: List[FileInfo]

class SuccessModel(BaseModel):
    message: str

class ErrorModel(BaseModel):
    detail: str

class LoginSuccessModel(BaseModel):
    message: str
    access_token: str
    token_type: str

class DownloadModel(BaseModel):
    download_url: str
    valid_for_seconds: int

class Files(BaseModel):
    count: int
    file_ids: List[UUID]
class BulkDeleteResponse(BaseModel):
    deleted_files: Files 
    files_not_found: Files
