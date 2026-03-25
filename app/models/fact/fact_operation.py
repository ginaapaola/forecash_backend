from sqlalchemy import Boolean, Column, Enum,  ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.models.dimensions.operation_type import OperationType


class FactOperation(Base):
    """
    Tabla de hechos central del star schema.
 
    Cada fila representa una operación financiera (venta, compra o gasto)
    generada a partir de un RawRecord durante el proceso ETL.
 
    Trazabilidad:
        FactOperation.raw_record_id → RawRecord.row_payload (dato original)
        FactOperation.raw_dataset_id → RawDataset (archivo fuente)
 
    Montos en Numeric(14, 2) para evitar errores de punto flotante
    con valores en pesos colombianos.
    """
    __tablename__ = "fact_operations"

    id = Column(Integer, primary_key=True, index=True)
    raw_record_id = Column(Integer, ForeignKey("raw_records.id", ondelete="CASCADE"), nullable=False, unique=True)
    raw_dataset_id = Column(Integer, ForeignKey("raw_datasets.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False, index=True)
    operation_type = Column(
        Enum(OperationType, name="operation"),
        nullable=False,
        index=True
    )

    concept = Column(String, nullable=True)
    quantity = Column(Numeric(10, 3), nullable=False, default=1)
    unit_price = Column(Numeric(14, 2), nullable=True)
    inlcudes_iva = Column(Boolean, default=False)
    iva_rate = Column(Numeric(5,4), nullable=False, default=0)
    subtotal = Column(Numeric(14, 2), default=0)
    total_amount = Column (Numeric(14, 2), nullable=False)


    dim_date_id = Column(Integer, ForeignKey("dim_dates.id", ondelete="CASCADE"), nullable=False)
    dim_product_id = Column(Integer, ForeignKey("dim_products.id", ondelete="CASCADE"), nullable=True)
    dim_category_id = Column(Integer, ForeignKey("dim_categories.id", ondelete="CASCADE"), nullable=True)
    dim_client_id = Column(Integer, ForeignKey("dim_clients.id", ondelete="CASCADE"), nullable=True)
    dim_supplier_id = Column(Integer, ForeignKey("dim_suppliers.id", ondelete="CASCADE"), nullable=True)
    dim_payment_id = Column(Integer, ForeignKey("dim_payments.id", ondelete="CASCADE"), nullable=True)

    #Relaciones
    dim_date = relationship("DimDate", back_populates="fact_operation")
    dim_product = relationship("DimProduct", back_populates="fact_operation")
    dim_category = relationship("DimCategory", back_populates="fact_operation")
    dim_client = relationship("DimClient", back_populates="fact_operation")
    dim_supplier = relationship("DimSupplier", back_populates="fact_operation")
    dim_payment = relationship("DimPayment", back_populates="fact_operation")

    __table_args__ = (
        Index("ix_fact_ops_company_date",   "company_id",   "dim_date_id"),
        Index("ix_fact_ops_company_type",   "company_id",   "operation_type"),
        Index("ix_fact_ops_dataset",        "raw_dataset_id"),
    )
 
    def __repr__(self) -> str:
        return (
            f"<FactOperation id={self.id} "
            f"type={self.operation_type}>"
        )