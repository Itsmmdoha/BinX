from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool
from typing import List
import boto3
import os
from datetime import datetime

app = FastAPI()

# In-memory list of file metadata
file_metadata: List[dict] = []

# MinIO config
MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "minioadmin"
SECRET_KEY = "minioadmin"
BUCKET_NAME = "uploads"

# Boto3 client for MinIO
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


@app.get("/")
def get_metadata():
    return file_metadata


@app.post("/")
async def upload_file(file: UploadFile = File(...)):
    file_name = file.filename

    try:
        # Run the upload_fileobj via the threadpool and await it
        await run_in_threadpool( 
            s3_client.upload_fileobj,   
            file.file,
            BUCKET_NAME,
            file_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to MinIO: {str(e)}")

    metadata = {
        "filename": file_name,
        "content_type": file.content_type,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
    }

    file_metadata.append(metadata)
    return {"message": "File uploaded successfully", "metadata": metadata}


@app.get("/file/{file_name}")
def get_file_link(file_name: str):
    found = next((f for f in file_metadata if f["filename"] == file_name), None)
    if not found:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': file_name},
            ExpiresIn=600  # 10 minutes
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

    return RedirectResponse(presigned_url)
