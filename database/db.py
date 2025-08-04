from datetime import  datetime, timezone 
from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import Index

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import uuid
from uuid_extensions import uuid7
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from config import DATABASE_URL

MB = 1024 * 1024
GB = MB * 1024

class Base(DeclarativeBase):
    pass

class Vault(Base):
    __tablename__ = "vaults"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vault: Mapped[str] = mapped_column(unique=True)
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    password_hash: Mapped[str] = mapped_column(String(60))
    size: Mapped[int] = mapped_column(BigInteger, default=500*MB) # Size in bytes, default is 500 MB
    used_storage: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"Vault(id={self.id!r}, vault={self.vault!r}, date_created={self.date_created!r},size={self.size!r}, used_storage={self.used_storage!r}, password_hash={self.password_hash!r})"

class File(Base):
    __tablename__ = "files"
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default= lambda: uuid7(),
        unique=True
    )
    visibility: Mapped[str] = mapped_column(default="private")
    vault_id: Mapped[int] = mapped_column(
        ForeignKey("vaults.id", ondelete="CASCADE"), 
        nullable=False
    )
    file: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(BigInteger)# Size in bytes
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_files_vault_id_id", "vault_id", "id"), # multicolumn index on vault_id & file_id 
    )

    def __repr__(self) -> str:
        return f"file(id={self.id!r}, visibility={self.visibility!r},vault_id={self.vault_id!r},  file={self.file!r}, size={self.size!r}, date_created={self.date_created!r})"

class Upload(Base):
    __tablename__ = "uploads"
    file_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default= lambda: uuid7(),
        unique=True
    )
    vault_id: Mapped[int] = mapped_column(
        ForeignKey("vaults.id", ondelete="CASCADE"), 
        nullable=False
    )
    object_upload_id: Mapped[str] # upload id from s3
    file: Mapped[str] = mapped_column(String(255))
    size: Mapped[int] = mapped_column(BigInteger)# Size in bytes
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_uploads_vault_id_file_id", "vault_id", "file_id"), # multicolumn index on vault_id & file_id 
    )

    def __repr__(self) -> str:
        return f"Upload(file_id={self.file_id!r},vault_id={self.vault_id!r}, upload_id={self.object_upload_id!r},  file={self.file!r}, size={self.size!r}, date_created={self.date_created!r})"


class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vault_id: Mapped[int] = mapped_column(
        ForeignKey("vaults.id", ondelete="CASCADE"), 
        nullable=False
    )
    file_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("uploads.file_id", ondelete="CASCADE"), 
        nullable=False
    )
    part_number: Mapped[int]
    etag: Mapped[str] = mapped_column(String(64))

    __table_args__ = (
        Index("ix_chunks_vault_id_file_id", "vault_id", "file_id"), # multicolumn index on vault_id & file_id 
    )

    def __repr__(self) -> str:
        return f"Chunk(id={self.id!r}, vault_id={self.vault_id!r}, part_number={self.part_number!r}, etag={self.etag!r})"


engine = create_engine(
    DATABASE_URL, echo=True,
    pool_pre_ping=True, # check if connection is dead before pooling 
    pool_recycle=300
)
Base.metadata.create_all(engine) # Creates all tables defined by models in Base.metadata, if they don't exist already



def get_session():
    with Session(engine) as session:
        yield session  # session automatically closes when done


