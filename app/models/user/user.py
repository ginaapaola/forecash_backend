from sqlalchemy import Column, DateTime, Integer, String, Enum, func
from sqlalchemy.orm import relationship
from app.core.db.base import Base
from app.models.user.user_role import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(
        Enum(UserRole, name="user_role"),
        nullable=False
    )

    phone = Column(String, unique=True, nullable=False)
    document_type = Column(String, nullable=False)
    document_number = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    companies = relationship("UserCompany", back_populates="user")


