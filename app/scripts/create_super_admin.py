from sqlalchemy.orm import Session
from app.core.db.session import SessionLocal
from app.core.config import settings
from app.core.security import hash_password
from app.models.user.user import User, UserRole, UserDocType
from app.models.user_company import user_empresa
from app.core.db.database import SessionLocal
from app.models.dimensions.operation_type import OperationType
from app.models.dimensions.dim_date import DimDate
from app.models.dimensions.dim_category import DimCategory
from app.models.dimensions.dim_client import DimClient
from app.models.dimensions.dim_payment import DimPayment
from app.models.dimensions.dim_product import DimProduct
from app.models.dimensions.dim_supplier import DimSupplier
from app.models.fact.fact_operation import FactOperation
from app.models.dataset.raw_dataset import RawDataset
from app.models.dataset.raw_record import RawRecord


def create_super_admin(): 

    print("entrando al create")
    db: Session = SessionLocal()

    print("conectando a:", settings.DATABASE_URL)

    print("users actuales: ", db.query(User).count())



    existing_admin = db.query(User).filter(
        User.role == UserRole.SUPER_ADMIN
    ).first()

    if(existing_admin):
        print("Super admin already exists")
        db.close()
        return 
    
    admin = User(
        name = settings.SUPERADMIN_NAME,
        email = settings.SUPERADMIN_EMAIL,
        password_hash = hash_password(settings.SUPERADMIN_PASS),
        role = UserRole.SUPER_ADMIN,
        phone = settings.SUPERADMIN_PHONE,
        document_type = settings.SUPERADMIN_DOC_TYPE,
        document_number = settings.SUPERADMIN_DOC_NUM
    )

    db.add(admin)
    try:
        db.commit()
    except Exception as e:
        print("ERROR: ", e)
        db.rollback()
    
    db.close()

    print("Super admin created successfully")

create_super_admin()