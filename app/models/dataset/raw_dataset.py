from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.models.dataset.dataset_enum import DatasetStatus, FileType, OperationTypeDataset


class RawDataset(Base):
    """
    Representa un archivo cargado por el usuario (CSV o XLSX).
    Actúa como cabecera del staging; los datos fila por fila
    se guardan en RawRecord.
 
    Relación con el MER:
        Company 1:M RawDataset  (vía company_id)
        User    M:1 RawDataset  (vía uploaded_by — quién hizo la carga)
        RawDataset 1:M RawRecord (relación 'contains' del MER)
        RawDataset 1:1 FactOperation (relación 'generate' — a través del ETL)
    """
    __tablename__ = "raw_datasets"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(
        Integer,
        ForeignKey("company.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    uploaded_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    file_name = Column(String, nullable=False)
    file_type = Column(
        Enum(FileType, name="file_type"),
        nullable=False
    )

    operation_type = Column(
        Enum(OperationTypeDataset, name="operation_type"),
        nullable=False,
        index=True
    )

    status = Column(
        Enum(DatasetStatus, name="dataset_status"),
        nullable=False,
        index=True,
        default=DatasetStatus.pending
    )
    
    column_mapping = Column(JSONB, nullable=True)
    etl_summary    = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    #relaciones
    
    company = relationship("Company", back_populates="raw_datasets")
    uploaded_by_user = relationship("User", foreign_keys=[uploaded_by])
    raw_record = relationship("RawRecord", back_populates="raw_dataset", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_raw_datasets_company_status", "company_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<RawDataset id={self.id} file={self.file_name} status={self.status}>"