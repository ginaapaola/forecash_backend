from sqlalchemy import Column, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.models.company.company import Company
from app.models.user_company.company_role import CompanyRole


class UserCompany(Base):
    __tablename__ = "user_company"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)
    role = Column(
        Enum(CompanyRole, name="company_role"),
        nullable=False
    )

    user = relationship('User', back_populates = "companies")
    company = relationship(Company, back_populates = "users")

    __table_args__ = (
        UniqueConstraint('user_id', 'company_id', name = 'uq_user_empresa'),
    )