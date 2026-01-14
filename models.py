import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    ForeignKey,
    BigInteger,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from db import Base


class Ingest(Base):
    __tablename__ = "ingests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_hash = Column(String(128), unique=True, nullable=False)
    file_name = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    total_rows = Column(Integer, default=0)
    inserted_rows = Column(Integer, default=0)


class Log(Base):
    __tablename__ = "logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ingest_id = Column(PGUUID(as_uuid=True), ForeignKey("ingests.id"), nullable=False, index=True)
    timestamp = Column(DateTime, index=True, nullable=True)
    module = Column(String(128), index=True, nullable=True)
    level = Column(String(32), index=True, nullable=True)
    message = Column(Text, nullable=True)
    row_hash = Column(String(128), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("row_hash", name="uq_logs_row_hash"),)
