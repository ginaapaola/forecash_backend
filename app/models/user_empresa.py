from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.models.company.company import Company


class UserCompany(Base):
    __tablename__ = "user_company"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    company_id = Column(Integer, ForeignKey('company.id'))

    user = relationship('User', back_populates = "companies")
    company = relationship(Company, back_populates = "users")

    __table_args__ = (
        UniqueConstraint('user_id', 'company_id', name = 'uq_user_empresa'),
    )