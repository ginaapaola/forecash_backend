from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.models.company.company import Company
from app.models.user_company.company_role import CompanyRole
from app.models.user_company.user_empresa import UserCompany
from app.schemas.request_schema.select_company import SelectCompanyRequest
from app.schemas.request_schema.tax_configuration import TaxConfiguration
from app.schemas.response_schema.company_response import CompanyResponse
from app.schemas.response_schema.user_basic_response import UserBasicResponse


class CompanyService:
    
    @staticmethod
    def get_company_id(db: Session, company_id):
        company = (
            db.query(Company)
            .options(
                joinedload(Company.users_companies)
                .joinedload(UserCompany.user)
            )
            .filter(Company.id == company_id)
            .first()
        )

        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        users_response = [
            UserBasicResponse(
                id=relacion.user.id,
                name=relacion.user.name,
                email=relacion.user.email,
                document_number=relacion.user.document_number
            )
            for relacion in company.users_companies
        ]

        return CompanyResponse(
            id=company.id,
            legal_name=company.legal_name,
            trade_name=company.trade_name,
            nit=company.nit,
            economic_sector=company.economic_sector,
            economic_activity=company.economic_activity,
            entity_type=company.entity_type,
            is_legally_constituted=company.is_legally_constituted,
            regime_type=company.regime_type,
            tax_rate=company.tax_rate,
            is_vat_responsible=company.is_vat_responsible,
            users=users_response
        )
    
    @staticmethod
    def get_companies(db: Session):
        companies = db.query(Company).all()

        if companies is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="NOT FOUND"
            )
        
        if companies.count == 0:
            return "There aren't companies yet"
        
        return companies
    
    @staticmethod
    def select_company(db: Session, data: SelectCompanyRequest, user_id):
        
        relation = (
            db.query(UserCompany)
            .filter(
                UserCompany.user_id == user_id,
                UserCompany.company_id == data.company_id
            )
            .first()
        )

        if not relation: 
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="User does not belong to this company"
            )
        
        return {
            "company_id": relation.company_id,
            "role": relation.role
        }
    
    @staticmethod
    def update_tax_config(db: Session, company_data: dict, data: TaxConfiguration):
        company = company_data["company"]
        role = company_data["role"]

        if not company.is_legally_constituted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tax configuration is only available for legally constituted companies"
            )

        if role != CompanyRole.LEGAL_REPRESENTATIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You aren't authorized to this action"
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)

        try:
            db.commit()
            db.refresh(company)
        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error updating tax information"
            )

        return company