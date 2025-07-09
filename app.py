from hashlib import new
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import object_session
from sqlalchemy.util import decode_backslashreplace
from starlette.concurrency import run_in_threadpool
from starlette.responses import RedirectResponse
from typing import Callable
from enum import Enum

from database import Vault, File, get_session
from s3 import s3_client, bucket_exists, S3_BUCKET_NAME
from config import FRONTEND_HOST
from sqlalchemy import select, delete, and_
from auth import Password, Token
from models.request import VaultCreateCredentials, VaultLoginCredentials, FileUpdateModel, VaultUpdateModel, BulkDeleteRequest
from models.response import SuccessModel, ErrorModel, LoginSuccessModel, DownloadModel, VaultModel, BulkDeleteResponse 
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_HOST],# Allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer()

def get_token_payload(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    token = credentials.credentials
    try:
        payload = Token.get_payload(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or Expired Token")

if bucket_exists():
    pass
else:
    print("Bucket doesn't exist")
    exit()

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
        payload = {"vault": vault.vault, "vault_id": vault.id, "role":"guest"}
        token = Token.generate(payload, valid_for=12*3600)
        return {"message": "Login as guest successful", "access_token": token, "token_type": "bearer"}
    elif Password.is_valid(password=vault_credentials.password, hash_string=vault.password_hash):
        payload = {"vault": vault.vault, "vault_id": vault.id, "role":"owner"}
        token = Token.generate(payload, valid_for=12*3600)
        return {"message": "Login successful", "access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.get("/vault/fetch",
    tags=["Vault Operations"],
    response_model=VaultModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel}
    }
)
def fetch_file_list_from_vault(
        token_payload: dict = Depends(get_token_payload),
        db_session = Depends(get_session)
):
    vault_id= token_payload.get("vault_id")
    role = token_payload.get("role")
    vault = db_session.scalars(select(Vault).where(Vault.id==vault_id)).first()
    if vault is None:
        raise HTTPException(status_code=404, detail="Vault Not Found")
    files_stmt = select(File)
    if role == Role.GUEST:
        files_stmt = files_stmt.where(and_(File.vault_id== vault_id, File.visibility == "public"))
    elif role == Role.OWNER:
        files_stmt = files_stmt.where(File.vault_id == vault_id) # All Files, without any filter
    files = db_session.scalars(files_stmt).all()
    return {"vault": vault, "files": files}

@app.put("/vault",
    tags=["Vault Operations"],
    response_model=SuccessModel,
    description="""
This endpoint allows you to perform the following actions on a vault:

1. **Rename the vault**  
2. **Change the vault's password**

- To **rename** the vault, include the `new_name` field in the request body.  
- To **change password**, include the `new_password` field in the request body.  
- To perform **both actions**, include both attributes in the same request.
    """,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel}
    }
)
def update_vault(
        update_data: VaultUpdateModel,
        token_payload: dict = Depends(get_token_payload),
        db_session = Depends(get_session)
):
    vault_id= token_payload.get("vault_id")
    role = token_payload.get("role")
    if role != Role.OWNER:
        raise HTTPException(status_code=401, detail="Not Authorized")
    stmt = select(Vault).where(Vault.id == vault_id)
    vault = db_session.scalars(stmt).first()
    if vault is None:
        raise HTTPException(status_code=404, detail="Vault Not Found")
    if update_data.new_name:
        vault.vault = update_data.new_name
    if update_data.new_password:
        vault.password_hash = Password.generate_hash(update_data.new_password)
    db_session.commit()
    return {"message": "Vault Information Updated successfully"}


@app.delete("/vault",
    tags=["Vault Operations"],
    response_model=SuccessModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel}
    }
)
def delete_vault(
        token_payload: dict = Depends(get_token_payload),
        db_session = Depends(get_session)
):
    vault_id= token_payload.get("vault_id")
    role = token_payload.get("role")
    if role != Role.OWNER:
        raise HTTPException(status_code=401, detail="Not Authorized")
    try:
        stmt = select(File.id).where(File.vault_id == vault_id)
        # fetch ids of stored files
        file_ids_to_delete = db_session.scalars(stmt).all()
        # delete from database
        stmt = delete(Vault).where(Vault.id == vault_id)
        db_session.execute(stmt)
        # delete from s3
        delete_keys = {"Objects": [{"Key": str(file_id)} for file_id in file_ids_to_delete]}
        s3_client.delete_objects(Bucket = S3_BUCKET_NAME, Delete=delete_keys)
        # commit deletes in database
        db_session.commit()
        return {"message": "Vault Deleted successfully"}
    except:
        raise HTTPException(status_code=401, detail="Not Authorized")




@app.post("/file/upload",
    tags=["File Operations"],
    response_model=SuccessModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        507: {"model": ErrorModel},
        500: {"model": ErrorModel}
    }
)
async def upload_file(
        token_payload: dict = Depends(get_token_payload),
        _: None = Depends(require_role(Role.OWNER)),
        db_session=Depends(get_session),
        file: UploadFile = FastAPIFile(...)
):
    vault_id = token_payload.get("vault_id")
    file_name = file.filename
    # Get file size without loading file into memory
    file.file.seek(0, 2)  
    file_size = file.file.tell()
    file.file.seek(0)  

    stmt = select(Vault).where(Vault.id==vault_id)
    vault = db_session.scalars(stmt).first()
    vault_size = vault.size
    used_storage = vault.used_storage
    if (used_storage + file_size) > vault_size:
        raise HTTPException(status_code=507, detail="Insufficient Storage")
    try:
        # store file metadata
        new_file = File(vault_id = vault_id, file = file_name, size=file_size)
        db_session.add(new_file)
        vault.used_storage += file_size
        db_session.commit()

        # Run the upload_fileobj via the threadpool and await it
        file_key = str(new_file.id)
        await run_in_threadpool( 
            s3_client.upload_fileobj,   
            file.file,
            S3_BUCKET_NAME,
            file_key
        )
    except Exception as e:
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
    vault_id = token_payload.get("vault_id")
    role = token_payload.get("role")
    stmt = select(File).where(and_(File.vault_id == vault_id, File.id==file_id))
    if role == Role.GUEST:
        stmt = stmt.where(File.visibility == "public") # if role is guest, only allow public files
    file = db_session.scalars(stmt).first()
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")

    valid_for = 60*10 # 10 minutes
    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': str(file_id), 'ResponseContentDisposition': f'attachment; filename="{file.file}"'},
            ExpiresIn= valid_for,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Error Generating Download Link}")

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
    vault_id = token_payload.get("vault_id")
    stmt = select(File).where(and_(File.vault_id == vault_id, File.id == file_id))
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
    vault_id = token_payload.get("vault_id")
    stmt = select(File).where(and_(File.vault_id == vault_id, File.id== file_id))
    file = db_session.scalars(stmt).first()
    if file:
        db_session.delete(file)
        find_vault_stmt = select(Vault).where(Vault.id == vault_id)
        vault = db_session.scalars(find_vault_stmt).first()
        vault.used_storage-=file.size
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=str(file_id))
        db_session.commit()
        return {"message":"file deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.post("/file/bulk-delete",
    tags=["File Operations"],
    response_model=BulkDeleteResponse,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
        500: {"model": ErrorModel},
    }
)
async def bulk_delete(
        file_ids: BulkDeleteRequest, 
        token_payload: dict = Depends(get_token_payload),
        _: None = Depends(require_role(Role.OWNER)),
        db_session = Depends(get_session)
):
    vault_id = token_payload.get("vault_id")
    stmt = select(File).where(File.id.in_(file_ids.file_ids))
    files_to_delete = db_session.scalars(stmt).all()
    if len(files_to_delete) == 0:
        raise HTTPException(status_code=404, detail="No files found")
    file_ids_to_delete = []
    freed_space = 0
    for file in files_to_delete:
        file_ids_to_delete.append(file.id)
        freed_space += file.size
    files_not_found = list(set(file_ids.file_ids) - set(file_ids_to_delete))

    try:
        # delete from database 
        delete_stmt = delete(File).where(File.id.in_(file_ids_to_delete))
        db_session.execute(delete_stmt)
        
        # Delete from s3 
        delete_keys = {"Objects": [{"Key": str(file_id)} for file_id in file_ids_to_delete]}
        s3_client.delete_objects(Bucket = S3_BUCKET_NAME, Delete=delete_keys)

        # update_used_storage
        vault_stmt = select(Vault).where(Vault.id==vault_id)
        vault = db_session.scalars(vault_stmt).first()
        vault.used_storage = vault.used_storage - freed_space
        db_session.commit()
        return {"deleted_files":{"count":len(file_ids_to_delete), "file_ids":file_ids_to_delete}, "files_not_found": {"count": len(files_not_found), "file_ids": files_not_found}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk Deletion Failed, error:{e}")

@app.get(
    "/{vault_name}/file/{file_id}",
    tags=["File Operations"],
    response_class=RedirectResponse,
    status_code=307,  # temporary redirect
    responses={
        403: {"model": ErrorModel},
        404: {"model": ErrorModel},
        500: {"model": ErrorModel},
    }
)
async def get_file_from_url(
    vault_name: str,
    file_id: UUID,
    db_session = Depends(get_session),
):
    stmt = select(Vault).where(Vault.vault == vault_name)
    vault_id = db_session.scalars(stmt).first().id
    stmt = select(File).where(
        and_(
            File.vault_id == vault_id,
            File.id == file_id
        )
    )
    file = db_session.scalars(stmt).first()
    if file is None:
        raise HTTPException(404, "File not found")
    if file.visibility == "private":
        raise HTTPException(403, "This file is private")

    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": str(file_id),
                "ResponseContentDisposition": f'attachment; filename="{file.file}"'
            },
            ExpiresIn=60 * 10,  # 10 minutes
        )
    except Exception:
        raise HTTPException(500, "Error generating download link")

    return RedirectResponse(url=presigned_url, status_code=307)
