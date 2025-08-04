from http.client import HTTP_PORT
from fastapi import APIRouter, Depends, UploadFile, File as fastapiFile, Form, HTTPException
from uuid import UUID

import fastapi
from database import Vault, File, Upload, Chunk, get_session
from s3 import s3_client
from config import S3_BUCKET_NAME
from utils import get_token_payload, require_role
from models.shared import Role
from models.request import MultipartFile
from models.response import MultipartInitiate, SuccessModel, ErrorModel
from sqlalchemy import select, update, and_
from typing import Annotated
from starlette.concurrency import run_in_threadpool

multipart_router = APIRouter(prefix="/file/multipart", tags=["Multipart Upload"])

@multipart_router.post("/initiate",
    response_model=MultipartInitiate,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        507: {"model": ErrorModel},
        500: {"model": ErrorModel}
    }
)
async def initiate_multipart_upload(
    file_info: MultipartFile,
    token_payload: dict = Depends(get_token_payload),
    _: None = Depends(require_role(Role.OWNER)),
    db_session = Depends(get_session)
):
    vault_id = token_payload.get("vault_id")
    stmt = select(Vault).where(Vault.id==vault_id)
    vault = db_session.scalars(stmt).first()
    vault_size = vault.size
    used_storage = vault.used_storage
    if (used_storage + file_info.file_size) > vault_size:
        raise HTTPException(status_code=507, detail="Insufficient Storage")
    try:
        new_upload = Upload(vault_id = vault_id, file = file_info.file_name, size=file_info.file_size)
        db_session.add(new_upload);
        db_session.flush()  # <-- Forces DB to assign the UUID before we use it
        s3_response = await run_in_threadpool(
            s3_client.create_multipart_upload,
            Bucket=S3_BUCKET_NAME,
            Key=str(new_upload.file_id),
            Metadata={"vault_id": str(vault_id), "filename": file_info.file_name}
        )
        new_upload.object_upload_id = s3_response["UploadId"]
        db_session.commit()
        return {"message": "Multipart upload initiated Successfully", "file_id": new_upload.file_id}
    except Exception as e:
        db_session.rollback()
        raise HTTPException(status_code=500,detail="Could not initiate Multipart Upload")




@multipart_router.put("/{file_id}/chunk",
    response_model=SuccessModel,
    responses={
        400: {"model": ErrorModel},
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        500: {"model": ErrorModel}
    }
)
async def upload_chunk(
    file_id: UUID,
    part_number: Annotated[int, Form()],
    blob: Annotated[UploadFile, fastapiFile()],
    token_payload: dict = Depends(get_token_payload),
    _: None = Depends(require_role(Role.OWNER)),
    db_session = Depends(get_session)
):
    vault_id = token_payload.get("vault_id")

    # Get chunk size
    blob.file.seek(0, 2)
    chunk_size = blob.file.tell()
    blob.file.seek(0)

    MIN_CHUNK_SIZE = 5 * 1024 * 1024  # 5 MB
    if(part_number ==1 and chunk_size<MIN_CHUNK_SIZE):
        raise HTTPException(status_code=400, detail="Chunk too small. Minimum is 5 MB.")

    stmt = select(Upload.object_upload_id).where(and_(Upload.vault_id == vault_id, Upload.file_id == file_id))
    upload_id = db_session.scalars(stmt).first()
    try:
        # Upload part to S3
        response = await run_in_threadpool(
            s3_client.upload_part,
            Bucket=S3_BUCKET_NAME,
            Key=str(file_id), 
            PartNumber=part_number,
            UploadId=upload_id,
            Body=blob.file  
        )
        etag = response["ETag"]

        # Store chunk metadata in DB
        new_chunk = Chunk(
            vault_id=vault_id,
            file_id=file_id,
            chunk_size=chunk_size,
            part_number=part_number,
            etag=etag
        )
        db_session.add(new_chunk)
        db_session.commit()

        return {"message" : "Chunk uploaded successfully"}
    except Exception as e:
        db_session.rollback()
        raise HTTPException(status_code=500, detail="Chunk upload failed")



@multipart_router.post("/{file_id}/complete",
    response_model=SuccessModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        507: {"model": ErrorModel},
        500: {"model": ErrorModel}
    }
)
async def complete_multipart_upload(
    file_id: UUID,
    token_payload: dict = Depends(get_token_payload),
    _: None = Depends(require_role(Role.OWNER)),
    db_session = Depends(get_session)
):
    vault_id = token_payload.get("vault_id")

    # Fetch upload metadata
    stmt = select(Upload).where(
        and_(Upload.vault_id == vault_id, Upload.file_id == file_id)
    )
    upload = db_session.scalars(stmt).first()

    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    upload_size = upload.size
    upload_id = upload.object_upload_id

    # Fetch chunk metadata
    stmt = select(Chunk.etag, Chunk.part_number, Chunk.chunk_size).where(
        and_(Chunk.vault_id == vault_id, Chunk.file_id == file_id)
    )
    chunks = db_session.execute(stmt).all()

    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks found")

    new_file = File(
        id = upload.file_id,
        vault_id = vault_id,
        file = upload.file,
        size = upload.size,
    )
    db_session.add(new_file)
    db_session.delete(upload)

    parts = []
    total_chunk_size = 0

    for etag, part_number, chunk_size in chunks:
        parts.append({
            "ETag": etag,
            "PartNumber": part_number
        })
        total_chunk_size += chunk_size

    # Verify size integrity
    if total_chunk_size != upload_size:
        raise HTTPException(status_code=400, detail="Total chunk size doesn't match original file size")

    try:
        # Complete multipart upload
        await run_in_threadpool(
            s3_client.complete_multipart_upload,
            Bucket=S3_BUCKET_NAME,
            Key=str(file_id),
            UploadId=upload_id,
            MultipartUpload={"Parts": sorted(parts, key=lambda p: p["PartNumber"])}  # Parts sorted in ascending order by PartNumber 
        )
        stmt = (
            update(Vault)
            .where(Vault.id == vault_id)
            .values(used_storage=Vault.used_storage + upload_size)
        )
        db_session.execute(stmt)
        db_session.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to complete multipart upload")

    return SuccessModel(
        message="File uploaded successfully",
    )



@multipart_router.delete("/{file_id}/abort",
    response_model=SuccessModel,
    responses={
        401: {"model": ErrorModel},
        403: {"model": ErrorModel},
        507: {"model": ErrorModel},
        500: {"model": ErrorModel}
    }
)
async def abort_multipart_upload(
    file_id: UUID,
    token_payload: dict = Depends(get_token_payload),
    _: None = Depends(require_role(Role.OWNER)),
    db_session = Depends(get_session)
):
    vault_id = token_payload.get("vault_id")
    stmt = select(Upload).where(and_(Upload.vault_id == vault_id, Upload.file_id == file_id))
    upload = db_session.scalars(stmt).first()
    if upload is None:
        raise HTTPException(status_code=404, detail="upload nof found")
    try:
        # Abort the multipart upload in S3
        await run_in_threadpool(
            s3_client.abort_multipart_upload,
            Bucket=S3_BUCKET_NAME,
            Key=str(upload.file_id),
            UploadId=str(upload.object_upload_id)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to abort multipart upload in S3")

    db_session.delete(upload)
    db_session.commit()
    return {"message": "multipart upload aborted"}
