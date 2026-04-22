from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.db.base import Base


class DimCategory(Base):
    """
    Dimensión de categorías (línea, grupo, familia del producto).
    """
    __tablename__ = "dim_categories"

    id  = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)

    #Relaciones
    fact_operation = relationship("FactOperation", back_populates="dim_category", lazy='noload')
    dim_product = relationship("DimProduct", back_populates="dim_category")

    