from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db.base import Base


class DimProduct(Base):
    """
    Dimensión de productos/artículos.
    El nombre del producto es la clave natural de deduplicación.
    """
    __tablename__ = "dim_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("dim_categories.id", ondelete="SET NULL"), nullable=True )
    
    #Relaciones
    fact_operation = relationship("FactOperation", back_populates="dim_product")
    dim_category = relationship("DimCategory", back_populates="dim_product", lazy='joined')

    __table_args__ = (
        UniqueConstraint("name", "company_id", name="uq_product_company"),
    )
 
    def __repr__(self) -> str:
        return f"<DimProduct name={self.name}>"