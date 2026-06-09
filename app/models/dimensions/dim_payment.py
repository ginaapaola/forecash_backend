from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.db.base import Base


class DimPayment(Base):
    """
    Dimensión de medios de pago (efectivo, tarjeta, transferencia, etc.).
    """
    __tablename__ = "dim_payments"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False, unique=True, index=True)

    #Relaciones
    fact_operation = relationship("FactOperation", back_populates="dim_payment")