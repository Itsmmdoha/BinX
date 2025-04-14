from fastapi import FastAPI, Depends, HTTPException, Response, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import boto3

from dbm import Vault, File as file_table, get_session
from auth_helper import Password, Token

class VaultInfo(BaseModel):
    vault: str
    password: str


app = FastAPI()

MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "uploads"

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
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.get("/")
def list_vaults(session = Depends(get_session)):
    return session.query(Vault).all()

@app.post("/vault/create")
def create_vault(vault_info: VaultInfo, db_session = Depends(get_session)):
    hashed_password = Password.generate_hash(vault_info.password)
    new_vault = Vault(vault=vault_info.vault, size=500*1024*1024, password_hash=hashed_password)
    db_session.add(new_vault)
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise HTTPException(status_code=409, detail=f"Already exists")
    return {"msg": "vault created successfully"}

@app.post("/vault/login")
def login(response: Response, vault_info: VaultInfo, db_session = Depends(get_session)):
    vault = db_session.query(Vault).filter(Vault.vault == vault_info.vault).first()
    if vault and Password.is_valid(password=vault_info.password, hash_string=vault.password_hash):
        payload = {"vault": vault.vault}
        token = Token.generate(payload, valid_for=12*3600)
        return {"message": "login successful", "access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.get("/vault/fetch")
def fetch_file_list(token_payload: dict = Depends(get_token_payload), db_session = Depends(get_session)):
    vault_name = token_payload.get("vault")
    files = db_session.query(file_table).filter(file_table.vault == vault_name).all()
    return files

@app.post("/file/upload")
async def file_upload(token_payload: dict = Depends(get_token_payload), db_session=Depends(get_session), file: UploadFile = File(...)):
    vault_name = token_payload.get("vault")
    file_name = file.filename
    try:
        # Get file size without loading file into memory
        file.file.seek(0, 2)  
        file_size = file.file.tell()
        file.file.seek(0)  

        # Run the upload_fileobj via the threadpool and await it
        file_key = str(vault_name) + str(file_name)
        await run_in_threadpool( 
            s3_client.upload_fileobj,   
            file.file,
            BUCKET_NAME,
            file_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to MinIO: {str(e)}")

    new_file = file_table(vault= vault_name, file = file_name, size=file_size)
    db_session.add(new_file)
    try:
        db_session.commit()
    except:
        db_session.rollback()
        return HTTPException(status_code=500, details="file upload failed")
    return {"message": "File uploaded successfully"}

@app.get("/file/download/{file_name}")
async def file_download(file_name: str, token_payload: dict = Depends(get_token_payload), db_session = Depends(get_session)):
    vault_name = token_payload.get("vault")
    file = db_session.query(file_table).filter(file_table.vault == vault_name and file_table.file== file_name).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': vault_name + file_name},
            ExpiresIn=600  # 10 minutes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

    print(presigned_url)
    return RedirectResponse(presigned_url)
    
@app.get("/file/delete/{file_name}")
async def file_delete(file_name: str, token_payload: dict = Depends(get_token_payload), db_session = Depends(get_session)):
    vault_name = token_payload.get("vault")
    file = db_session.query(file_table).filter(file_table.vault == vault_name and file_table.file== file_name).first()
    if file:
        db_session.delete(file)
        db_session.commit()
        return file
    else:
        return file
        raise HTTPException(status_code=404, detail="File not found")

