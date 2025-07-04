from datetime import  datetime, timezone 
from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import uuid
import uuid6
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
        return f"Vault(id={self.id!r}, vault={self.vault!r}, date_created={self.date_created!r},size={self.size!r}, password_hash={self.password_hash!r})"

class File(Base):
    __tablename__ = "files"
    file_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid6.uuid7,
        unique=True
    )
    visibility: Mapped[str] = mapped_column(default="private")
    vault: Mapped[str] = mapped_column(ForeignKey("vaults.vault"))
    file: Mapped[str] 
    size: Mapped[int] = mapped_column(BigInteger)# Size in bytes
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


    def __repr__(self) -> str:
        return f"file(id={self.file_id!r}, visibility={self.visibility!r},vault={self.vault!r},  file={self.file!r}, size={self.size!r}, date_created={self.date_created!r})"


engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine) # Creates all tables defined by models in Base.metadata, if they don't exist already



def get_session():
    with Session(engine) as session:
        yield session  # session automatically closes when done


