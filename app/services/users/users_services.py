from sqlalchemy.orm import joinedload

from app.models.user.user import User
from app.models.user.user_role import UserRole
from app.models.user_empresa import UserCompany
from app.schemas.response_schema.company_response import CompanyResponse
from app.schemas.response_schema.user_response import UserResponse

class UsersService:

    @staticmethod
    def get_user(db, user_id):
        user = (
            db.query(User)
            .options(
                joinedload(User.companies)
                .joinedload(UserCompany.company)
            )
            .filter(User.id == user_id)
            .first()
        )
        if not user: 
            raise Exception("User not found")
        
        if user.role == UserRole.SUPER_ADMIN:
            return UserResponse (
                id=user.id,
                name=user.name,
                email=user.email,
                role=user.role,
                phone=user.phone,
                document_type=user.document_type,
                document_number=user.document_number,
                companies=[]
            )
        
        empresas_response = [
            CompanyResponse(
                id=relacion.company.id,
                legal_name=relacion.company.legal_name,
                trade_name=relacion.company.trade_name,
                nit=relacion.company.nit,
                economic_sector=relacion.company.economic_sector,
                economic_activity=relacion.company.economic_activity,
                entity_type=relacion.company.entity_type,
                is_legally_constituted=relacion.company.is_legally_constituted
            )
            for relacion in user.companies
        ]

        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            phone=user.phone,
            document_type=user.document_type,
            document_number=user.document_number,
            companies=empresas_response
        )