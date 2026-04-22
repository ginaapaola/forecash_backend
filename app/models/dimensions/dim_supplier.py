from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db.base import Base


class DimSupplier(Base):
    """
    Dimensión de proveedores. Clave natural: nombre del proveedor.
    """
    __tablename__ = "dim_suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), index=True, nullable=False)

    #Relaciones
    fact_operation = relationship("FactOperation", back_populates="dim_supplier")

    __table_args__ = (
        UniqueConstraint("name", "company_id", name="uq_supplier_company"),
    )
 