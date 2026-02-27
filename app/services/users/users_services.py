from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_password, verify_password
from app.models.user.user import User
from app.models.user.user_role import UserRole
from app.models.user_company.user_empresa import UserCompany
from app.schemas.request_schema.auth_request import ChangePasswordRequest
from app.schemas.request_schema.user_request import UserRequestUpdate
from app.schemas.response_schema.company_response import CompanyResponse
from app.schemas.response_schema.user_response import UserResponse

class UsersService:

    @staticmethod
    def get_all_users(db:Session):
        users = db.query(User)

        if users is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NOT FOUND"
            )
        
        if users.count == 0:
            return "There aren't users yet"
        
        return users
    
    @staticmethod
    def get_user_email(db:Session):
        user = db.query(User).filter(User.email).first()

        if user is None: 
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NOT FOUND"
            )
        return user

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
    
    @staticmethod
    def update_user_password(db: Session, user_id, data:ChangePasswordRequest):
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user not found"
            )
        
        isMatch = verify_password(data.current_password, user.password_hash)

        if not isMatch:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="incorrect current password"
            )
        
        if verify_password(data.new_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        user.password_hash = hash_password(data.new_password)

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating password"
            )
        
        return {"message": "Password updated successfully"}
    
    @staticmethod
    def update_user(db: Session, user_id, data: UserRequestUpdate):
        user = db.query(User).filter(User.id == user_id).first()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user not found"
            )
        
        user.phone = data.phone

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating phone"
            )
        
        return {"message": "Phone updated successfully"}