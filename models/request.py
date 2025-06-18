from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from .shared import Visibility

class VaultCreateCredentials(BaseModel):
    vault: str
    password: str

class VaultLoginCredentials(BaseModel):
    vault: str
    password: Optional[str] = Field(None, description="Password for the vault, if provided, logs in as owner, otherwise guest.")

class FileUpdateModel(BaseModel):
    new_name: Optional[str] = Field(None, description="New file name")
    visibility: Optional[Visibility] = Field(None, description="File visibility")

class BulkDeleteRequest(BaseModel):
    file_ids: List[UUID] = Field(..., description="Array of file IDs to delete", max_length=100)
