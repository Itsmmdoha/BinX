from fastapi import FastAPI, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.concurrency import run_in_threadpool
import boto3
from typing import Callable
from enum import Enum

from database import Vault, File, get_session
from sqlalchemy import select, and_
from auth import Password, Token
from models.request import VaultCreateCredentials, VaultLoginCredentials, FileUpdateModel
from models.response import SuccessModel, ErrorModel, LoginSuccessModel, DownloadModel, VaultModel
from uuid import UUID

class Role(str, Enum):
    OWNER = "owner"
    GUEST = "guest"

def require_role(required_role: Role) -> Callable:
    def enforce_role(token_payload: dict = Depends(get_token_payload)):
        role = token_payload.get("role")
        if role != required_role:
            raise HTTPException(status_code=403, detail="Forbidden Operation")
    return enforce_role


app = FastAPI(title="BinX",version="0.0.1", redoc_url=None)

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


@app.post("/vault/create",
    tags=["Vault Operations"],
    response_model=SuccessModel,
    responses={
        409: {"model": ErrorModel}
    }
)
def create_vault(
        vault_credentials: VaultCreateCredentials,
        db_session = Depends(get_session)
):
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
    description="""
Login to a vault in one of two modes:

1. **Guest Mode** – Provides read-only access (view/download) to public files.  
   To log in as a guest, send only the `vaultname` in the request body.

2. **Owner Mode** – Grants full access including uploading, renaming, changing visibility, and deleting files.  
   To log in as an owner, send both the `vaultname` and the correct `password`.

If the credentials are valid, a **JWT Bearer Token** will be returned in the response.  
You must include this token in the `Authorization` header (`Bearer <token>`) to access protected endpoints that support read/write operations.
""",
    response_model=LoginSuccessModel, 
    responses={
        401: {"model": ErrorModel},
        404: {"model": ErrorModel},
        500: {"model": ErrorModel}
    }
)
def login_to_vault(
        vault_credentials: VaultLoginCredentials,
        db_session = Depends(get_session)
):
    stmt = select(Vault).where(Vault.vault == vault_credentials.vault)
    vault = db_session.scalars(stmt).first()

    if vault is None:
        raise HTTPException(status_code=404, detail="Vault Not Found")
    elif vault_credentials.password is None:
        payload = {"vault": vault.vault, "role":"guest"}
        token = Token.generate(payload, valid_for=12*3600)
        return {"message": "Login as guest successful", "access_token": token, "token_type": "bearer"}
    elif Password.is_valid(password=vault_credentials.password, hash_string=vault.password_hash):
        payload = {"vault": vault.vault, "role":"owner"}
        token = Token.generate(payload, valid_for=12*3600)
        return {"message": "Login successful", "access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.get("/vault/fetch",
    tags=["Vault Operations"],
    response_model=VaultModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel}
    }
)
def fetch_file_list_from_vault(
        token_payload: dict = Depends(get_token_payload),
        db_session = Depends(get_session)
):
    vault_name = token_payload.get("vault")
    role = token_payload.get("role")
    vault = db_session.scalars(select(Vault).where(Vault.vault==vault_name)).first()
    files_stmt = select(File)
    if role == Role.GUEST:
        files_stmt = files_stmt.where(and_(File.vault == vault_name, File.visibility == "public"))
    elif role == Role.OWNER:
        files_stmt = files_stmt.where(File.vault == vault_name) # All Files, without any filter
    files = db_session.scalars(files_stmt).all()
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
async def upload_file(
        token_payload: dict = Depends(get_token_payload),
        _: None = Depends(require_role(Role.OWNER)),
        db_session=Depends(get_session),
        file: UploadFile = FastAPIFile(...)
):
    vault_name = token_payload.get("vault")
    file_name = file.filename
    # Get file size without loading file into memory
    file.file.seek(0, 2)  
    file_size = file.file.tell()
    file.file.seek(0)  

    stmt = select(Vault).where(Vault.vault==vault_name)
    vault = db_session.scalars(stmt).first()
    vault_size = vault.size
    used_storage = vault.used_storage
    if (used_storage + file_size) > vault_size:
        return {"message": "not enough storage, please delete some files and try again"}

    try:
        # store file metadata
        new_file = File(vault= vault_name, file = file_name, size=file_size)
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
async def download_file(
        file_id: UUID,
        token_payload: dict = Depends(get_token_payload),
        db_session = Depends(get_session)
):
    vault_name = token_payload.get("vault")
    role = token_payload.get("role")
    stmt = select(File).where(and_(File.vault == vault_name, File.file_id==file_id))
    if role == Role.GUEST:
        stmt = stmt.where(File.visibility == "public") # if role is guest, only allow public files
    file = db_session.scalars(stmt).first()
    if file is None:
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
    description="""
This endpoint allows you to perform the following actions on a file:

1. **Rename a file**  
2. **Change the file's visibility** (public/private)

- To **rename** the file, include the `new_name` field in the request body.  
- To **change visibility**, include the `visibility` field (`"public"` or `"private"`) in the request body.  
- To perform **both actions**, include both attributes in the same request.
    """,
    response_model=SuccessModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
    }
)
async def update_file(
        file_id: UUID,
        update_data: FileUpdateModel,
        token_payload: dict = Depends(get_token_payload),
        _: None = Depends(require_role(Role.OWNER)),
        db_session = Depends(get_session)
):
    vault_name = token_payload.get("vault")
    stmt = select(File).where(and_(File.vault == vault_name, File.file_id == file_id))
    file = db_session.scalars(stmt).first()
    if file:
        if update_data.new_name is not None:
            file.file = update_data.new_name
        if update_data.visibility is not None:
            file.visibility = update_data.visibility
        db_session.commit()
        return {"message": "File updated successfully"}
    else:
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
async def delete_file(
        file_id: UUID,
        token_payload: dict = Depends(get_token_payload),
        _: None = Depends(require_role(Role.OWNER)),
        db_session = Depends(get_session)
):
    vault_name = token_payload.get("vault")
    stmt = select(File).where(and_(File.vault == vault_name, File.file_id== file_id))
    file = db_session.scalars(stmt).first()
    if file:
        db_session.delete(file)
        find_vault_stmt = select(Vault).where(Vault.vault == vault_name)
        vault = db_session.scalars(find_vault_stmt).first()
        vault.used_storage-=file.size
        db_session.commit()
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=str(file_id))
        return {"message":"file deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

