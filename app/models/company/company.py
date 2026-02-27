from sqlalchemy import Boolean, Column, Enum, Integer, String
from sqlalchemy.orm import relationship
from app.core.db.base import Base
from app.models.company.economic_sector import EconomicSector
from app.models.company.entity_type import EntityType


class Company(Base):
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    legal_name = Column(String, nullable=False)
    trade_name = Column(String, nullable=False)
    nit = Column(String, unique=True, nullable=False, index=True)
    economic_sector = Column(String, default="Servicios")
    economic_activity = Column(String, nullable=False)
    entity_type = Column(
        Enum(EntityType, name='entity_type'),
        nullable=False
    )
    is_legally_constituted = Column(Boolean, nullable=False)

    users = relationship("UserCompany", back_populates="company")