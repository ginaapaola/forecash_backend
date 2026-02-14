from sqlalchemy.orm import Session
from app.core.db.session import SessionLocal
from app.core.config import settings
from app.core.security import hash_password
from app.models.user.user import User, UserRole


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