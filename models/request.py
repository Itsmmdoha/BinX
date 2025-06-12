from pydantic import BaseModel, Field
from typing import Optional
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
