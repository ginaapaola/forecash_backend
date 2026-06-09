from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db.session import get_db
from app.dependencies.get_current_user import get_current_user
from app.models.user.user import User
from app.models.user.user_role import UserRole
from app.models.user_company.company_role import CompanyRole
from app.models.user_company.user_empresa import UserCompany


def require_role(required_role: CompanyRole):

    def dependency(
        company_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):

        # 🔥 Si es super admin, pasa automáticamente
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        relation = db.query(UserCompany).filter(
            UserCompany.user_id == current_user.id,
            UserCompany.company_id == company_id
        ).first()

        if not relation or relation.role != required_role:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos en esta empresa"
            )

        return current_user

    return dependency