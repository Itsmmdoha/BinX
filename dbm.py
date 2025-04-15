from datetime import datetime, timezone 
from sqlalchemy import DateTime
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_URL = "sqlite:///example.db"

class Base(DeclarativeBase):
    pass

class Vault(Base):
    __tablename__ = "vaults"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vault: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str] = mapped_column(String(60))
    size: Mapped[int] = mapped_column(default=500 * 1024 * 1024) # Size in bytes, default is 500 MB
    used_storage: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"Vault(id={self.id!r}, vault={self.vault!r}, size={self.size}, password_hash={self.password_hash!r})"

class File(Base):
    __tablename__ = "files"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    vault: Mapped[str] 
    file: Mapped[str] 
    size: Mapped[int] # Size in bytes
    date_created: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


    def __repr__(self) -> str:
        return f"file(id={self.id!r}, vault={self.vault!r},  file={self.file!r}, size={self.size!r}, date_created={self.date_created!r})"


engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine) # Creates all tables defined by models in Base.metadata, if they don't exist already



def get_session():
    with Session(engine) as session:
        yield session  # session automatically closes when done


if __name__ == "__main__":
    session = next(get_session()) # this is done automatically Depends(get_session) in FastAPI

    new_vault = Vault(vault="testName1", size=500, password_hash="hash_string_of_password")
    session.add(new_vault)
    try:
        session.commit()
    except:
        #if an exception is raised while commiting the data, like constraints(e.g. not unique), or IO failure, the commit is rolled back
        session.rollback()
        #then the connection is closed by the context manager(with) 

    print(session.query(Vault).all())


