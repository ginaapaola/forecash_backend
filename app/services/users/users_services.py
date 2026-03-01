from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import create_activation_token, generate_secure_pass, hash_password, verify_password
from app.models.company.company import Company
from app.models.user.user import User
from app.models.user.user_role import UserRole
from app.models.user_company.company_role import CompanyRole
from app.models.user_company.user_empresa import UserCompany
from app.schemas.request_schema.auth_request import ChangePasswordRequest
from app.schemas.request_schema.user_request import CreateUserRequest, UserRequestUpdate
from app.schemas.response_schema.company_response import CompanyResponse
from app.schemas.response_schema.user_response import UserResponse


class UsersService:

    @staticmethod
    async def get_all_users(db:Session):
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
    
    @staticmethod
    def create_user_for_company(db: Session, company_id, data: CreateUserRequest, user_id):

        # Verificar que la empresa exista
        company = db.query(Company).filter(Company.id == company_id).first()

        if company is None: 
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        #Verificar que el usuario es el representante legal de la empresa y no permitir la creación de otro rep_legal
        rep_relation = db.query(UserCompany).filter(
            UserCompany.user_id == user_id,
            UserCompany.company_id == company_id,
            UserCompany.role == CompanyRole.LEGAL_REPRESENTATIVE
        ).first()

        if rep_relation is None: 
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You aren't authorized to create users in this company"
            )
        
        if data.role == CompanyRole.LEGAL_REPRESENTATIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create another legal representative"
            )
        
        # Verificar si el nuevo usuario ya existe globalmente
        existing_user = db.query(User).filter(User.email == data.email).first()

        if existing_user:
            existing_in_company = db.quuery(UserCompany).filter(
                UserCompany.user_id == existing_user.id,
                UserCompany.company_id == company_id
            ).first()

            #Verificar que no exista dentro de la empresa para no generar duplicados
            if existing_in_company:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Users already exists in company"
                )
            
            new_relation = UserCompany(
                user_id=existing_user.id,
                company_id=company_id,
                role=data.role
            )

            db.add(new_relation)
            db.commit()
            db.refresh ()

            return existing_user
        
        # Si no existe globalmente, crearlo y relacionarlo en la empresa 
        generated_password = generate_secure_pass()
        hashed_password = hash_password(generated_password)

        new_user = User(
            name=data.name,
            email=data.email,
            phone=data.phone,
            document_type=data.document_type,
            document_number=data.document_number,
            password_hash=hashed_password,
            is_active=False
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        user_company = UserCompany(
            user_id=new_user.id,
            company_id=company_id,
            role=data.role
        )

        db.add(user_company)
        db.commit()

        #Generar token de activación
        activation_token = create_activation_token(new_user.id)

        return {
            "email": new_user.email,
            "username": new_user.document_number,
            "password": generated_password,
            "activation_token": activation_token
        }

