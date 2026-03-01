from sqlalchemy import Boolean, Column, DateTime, Integer, String, Enum, func
from sqlalchemy.orm import relationship
from app.core.db.base import Base
from app.models.user.doc_type import UserDocType
from app.models.user.user_role import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(
        Enum(UserRole, name="user_role"),
        nullable=True
    )

    phone = Column(String, unique=True)
    document_type = Column(
        Enum(UserDocType, name="document_type"),
        nullable=False
    )
    document_number = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=False, nullable=False)

    companies = relationship(
        "UserCompany", 
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


