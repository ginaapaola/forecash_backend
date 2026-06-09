from sqlalchemy import Column, Date, Index, Integer
from sqlalchemy.orm import relationship

from app.core.db.base import Base


class DimDate(Base):
    """
    Dimensión de tiempo.
    Se pre-popula o se genera en el ETL con get_or_create por full_date.
    Permite filtros por día, semana, mes y año en el dashboard (RF-005).
    """

    __tablename__ = "dim_dates"

    id = Column(Integer, primary_key=True, index=True)
    full_date = Column(Date, unique=True, nullable=False, index=True)
    day = Column(Integer, nullable=False)
    week = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    #Relaciones 
    fact_operation = relationship("FactOperation", back_populates="dim_date")

    __table_args__ = (
        Index("ix_dim_dates_year_month", "year", "month"),
    )
 
    def __repr__(self) -> str:
        return f"<DimDate {self.full_date}>"