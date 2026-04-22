from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db.base import Base


class DimClient(Base):

    """
    Dimensión de clientes. Clave natural: nombre del cliente.
    En negocios pequeños el nombre es el único dato disponible.
    """

    __tablename__ = "dim_clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), index=True, nullable=False)

    #Relaciones
    fact_operation = relationship("FactOperation", back_populates="dim_client")

    __table_args__ = (
        UniqueConstraint("name", "company_id", name="uq_client_company"),
    )