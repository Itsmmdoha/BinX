from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
import boto3
from datetime import datetime
from typing import List, Literal, Optional

from dbm import Vault, File as file_table, get_session
from auth_helper import Password, Token

from uuid import UUID

class VaultCreateCredentials(BaseModel):
    vault: str
    password: str

class VaultLoginCredentials(BaseModel):
    vault: str
    password: Optional[str] = Field(None, description="Password for the vault, if provided, logs in as owner, otherwise guest.")

class FileUpdateModel(BaseModel):
    new_name: Optional[str] = Field(None, description="New file name")
    visibility: Optional[Literal["private", "public"]] = Field(None, description="File visibility")

class FileVisibilityUpdate(BaseModel):
    visibility: Literal["private", "public"]
# Response Models
class VaultInfoModel(BaseModel):
    vault: str
    date_created: datetime
    size: int
    used_storage: int
    class Config:
        orm_mode = True
        
class FileInfo(BaseModel):
    file: str
    file_id: UUID 
    size: int
    date_created: datetime
    class Config:
        orm_mode = True

class vaultModel(BaseModel):
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


app = FastAPI()

MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "binx"

s3_client = boto3.client(
    "s3",
    endpoint_url=f"http://{MINIO_ENDPOINT}",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)

# Ensure bucket exists
try:
    s3_client.head_bucket(Bucket=BUCKET_NAME)
except:
    s3_client.create_bucket(Bucket=BUCKET_NAME)


bearer_scheme = HTTPBearer()

def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = Token.get_payload(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or Expired Token")

@app.get("/")
def list_vaults(session = Depends(get_session)):
    return session.query(Vault).all()

@app.post("/vault/create",
    tags=["Vault Operations"],
    response_model=SuccessModel,
    responses={
        409: {"model": ErrorModel}
    }
)
def create_vault(vault_credentials: VaultCreateCredentials, db_session = Depends(get_session)):
    hashed_password = Password.generate_hash(vault_credentials.password)
    new_vault = Vault(vault=vault_credentials.vault, password_hash=hashed_password)
    db_session.add(new_vault)
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise HTTPException(status_code=409, detail=f"Already exists")
    return {"message": "vault created successfully"}

@app.post("/vault/login",
    tags=["Vault Operations"],
    response_model=LoginSuccessModel, 
    responses={
        401: {"model": ErrorModel},
        404: {"model": ErrorModel}
    }
)
def login_to_vault(vault_credentials: VaultLoginCredentials, db_session = Depends(get_session)):
    vault = db_session.query(Vault).filter(Vault.vault == vault_credentials.vault).first()
    if not vault:
        raise HTTPException(status_code=404, detail="Vault Not Found")
    elif vault_credentials.password is None:
        payload = {"vault": vault.vault, "user":"guest"}
        token = Token.generate(payload, valid_for=12*3600)
        return {"message": "Login as guest successful", "access_token": token, "token_type": "bearer"}
    elif Password.is_valid(password=vault_credentials.password, hash_string=vault.password_hash):
        payload = {"vault": vault.vault, "user":"owner"}
        token = Token.generate(payload, valid_for=12*3600)
        return {"message": "Login successful", "access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.get("/vault/fetch",
    tags=["Vault Operations"],
    response_model=vaultModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel}
    }
)
def fetch_file_list_from_vault(token_payload: dict = Depends(get_token_payload), db_session = Depends(get_session)):
    vault_name = token_payload.get("vault")
    user = token_payload.get("user")
    vault = db_session.query(Vault).filter(Vault.vault==vault_name).first()
    files = db_session.query(file_table)
    if user == "guest":
        files= files.filter(file_table.vault == vault_name, file_table.visibility == "public").all()
    elif user == "owner":
        files= files.filter(file_table.vault == vault_name, file_table.visibility == "public", file_table.visibility==private).all()
    return {"vault": vault, "files": files}



@app.post("/file/upload",
    tags=["File Operations"],
    response_model=SuccessModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        500: {"model": ErrorModel}
    }
)
async def upload_file(token_payload: dict = Depends(get_token_payload), db_session=Depends(get_session), file: UploadFile = File(...)):
    if token_payload.get("user") != "owner":
        raise HTTPException(status_code=403, detail="Forbidden Operation")
    vault_name = token_payload.get("vault")
    file_name = file.filename
    # Get file size without loading file into memory
    file.file.seek(0, 2)  
    file_size = file.file.tell()
    file.file.seek(0)  

    vault = db_session.query(Vault).filter(Vault.vault==vault_name).first()
    vault_size = vault.size
    used_storage = vault.used_storage
    if (used_storage + file_size) > vault_size:
        return {"message": "not enough storage, please delete some files and try again"}

    try:
        # store file metadata
        new_file = file_table(vault= vault_name, file = file_name, size=file_size)
        db_session.add(new_file)
        vault.used_storage += file_size
        db_session.commit()

        # Run the upload_fileobj via the threadpool and await it
        file_key = str(new_file.file_id)
        await run_in_threadpool( 
            s3_client.upload_fileobj,   
            file.file,
            BUCKET_NAME,
            file_key
        )
    except Exception as e:
        print(e)
        db_session.rollback()
        raise HTTPException(status_code=500, detail="File Upload Failed")

    return {"message": "File uploaded successfully"}

@app.get("/file/{file_id}",
    tags=["File Operations"],
    response_model=DownloadModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
        500: {"model": ErrorModel}
    }
)
async def download_file(file_id: UUID, token_payload: dict = Depends(get_token_payload), db_session = Depends(get_session)):
    vault_name = token_payload.get("vault")
    files = db_session.query(file_table)
    file = files.filter(file_table.vault == vault_name, file_table.file_id==file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    valid_for = 60*10 # 10 minutes
    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': str(file_id), 'ResponseContentDisposition': f'attachment; filename="{file.file}"'},
            ExpiresIn= valid_for,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Error Generating Download Link}")

    print(presigned_url)
    return {"download_url": presigned_url, "valid_for_seconds":valid_for}

@app.put("/file/{file_id}",
    tags=["File Operations"],
    response_model=SuccessModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
    }
)
async def update_file(file_id: UUID, update_data: FileUpdateModel, token_payload: dict = Depends(get_token_payload), db_session = Depends(get_session)):
    if token_payload.get("user") != "uwner":
        raise HTTPException(status_code=403, detail="Forbidden Operation")
    vault_name = token_payload.get("vault")
    file = db_session.query(file_table).filter(file_table.vault == vault_name, file_table.file_id == file_id).first()
    if file:
        if update_data.new_name is not None:
            file.file = update_data.new_name
        if update_data.visibility is not None:
            file.visibility = update_data.visibility
        db_session.commit()
        return {"message": "File updated successfully"}
    else:
        db_session.rollback()
        raise HTTPException(status_code=404, detail="File not found")


@app.delete("/file/{file_id}",
    tags=["File Operations"],
    response_model=SuccessModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
    }
)
async def delete_file(file_id: UUID, token_payload: dict = Depends(get_token_payload), db_session = Depends(get_session)):
    if token_payload.get("user") != "uwner":
        raise HTTPException(status_code=403, detail="Forbidden Operation")
    vault_name = token_payload.get("vault")
    file = db_session.query(file_table).filter(file_table.vault == vault_name, file_table.file_id== file_id).first()
    if file:
        db_session.delete(file)
        vault = db_session.query(Vault).filter(Vault.vault == vault_name).first()
        vault.used_storage-=file.size
        db_session.commit()
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=str(file_id))
        return {"message":"file deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

