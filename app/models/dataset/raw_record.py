from sqlalchemy import Column, ForeignKey, Index, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.db.base import Base


class RawRecord(Base):
    """
    Fila individual de un archivo cargado, guardada como JSON crudo.
 
    Propósito de staging:
    - Guarda el dato tal como viene del CSV/XLSX, sin transformar.
    - Permite trazabilidad completa: cada FactOperation referencia
      el RawRecord que lo originó (relación 'originates' del MER).
    - Permite reprocesar el ETL sin volver a cargar el archivo.
    """

    __tablename__ = "raw_records"

    id = Column(Integer, primary_key=True, index=True)
    raw_dataset_id = Column(
        Integer,
        ForeignKey("raw_datasets.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
        index=True
    )
    row_number = Column(Integer, nullable=False)
    row_payload = Column(JSONB, nullable=False)
    #Relaciones
    raw_dataset = relationship("RawDataset", back_populates="raw_record")

    __table_args__ = (
        Index("ix_raw_records_dataset_row", "raw_dataset_id", "row_number"),
    )
 
    def __repr__(self) -> str:
        return f"<RawRecord dataset={self.raw_dataset_id} row={self.row_number}>"