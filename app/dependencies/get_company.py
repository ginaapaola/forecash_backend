"""Dependencia para resolver la empresa activa del request."""

from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.dependencies.get_current_user import get_current_user
from app.models.company.company import Company
from app.models.user_company.user_empresa import UserCompany

def get_company(
    x_company_id: int = Header(..., alias="X-Company-Id"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """Valida el header X-Company-Id y la pertenencia del usuario."""

    relation = (
        db.query(UserCompany)
        .filter(
            UserCompany.user_id == user.id,
            UserCompany.company_id == x_company_id
        )
        .first()
    )

    if not relation:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to this company"
        )

    company = (
        db.query(Company)
        .filter(Company.id == x_company_id)
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    return {
        "company": company,
        "role": relation.role
    }
