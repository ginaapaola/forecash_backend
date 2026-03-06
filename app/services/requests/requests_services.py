from typing import List
import uuid

from fastapi import BackgroundTasks, HTTPException, UploadFile, status
import json
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.security import create_activation_token, generate_secure_pass, hash_password
from app.core.firebase.firebase_config import bucket
from app.models.company.company import Company
from app.models.request.file import RequestFile
from app.models.request.register_request import RegisterRequest
from app.models.request.request_status import Status
from app.models.user.user import User
from app.models.user_company.company_role import CompanyRole
from app.models.user_company.user_empresa import UserCompany
from app.schemas.request_schema.register_request import CompanyRequestCreate, RegisterRequestUpdate
from app.services.email.email_service import EmailService

class RequestsServices:

    MAX_SIZE = 10 * 1024 * 1024
    ALLOWED_TYPES = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ]

    @staticmethod
    def create_request(
        db: Session,
        data: dict,
        files: List[UploadFile] = None
    ):
        try:
            data["usuarios_json"] = json.loads(
                data.get("usuarios_json", [])
            )
            validated_data = CompanyRequestCreate(**data)
                            
            request_dict = validated_data.model_dump()

            new_request = RegisterRequest(**request_dict)

            db.add(new_request)
            db.flush()

            #LOGICA DE ARCHIVOS
            if files:
                for file in files:

                    # 🔐 Validar tipo
                    if file.content_type not in RequestsServices.ALLOWED_TYPES:
                        raise Exception(f"Tipo de archivo no permitido: {file.content_type}")

                    # 🔐 Validar tamaño
                    file.file.seek(0, 2)
                    size = file.file.tell()
                    file.file.seek(0)

                    if size > RequestsServices.MAX_SIZE:
                        raise Exception("Archivo demasiado grande (máx 10MB)")

                    # 🔥 Generar nombre único
                    unique_name = f"{uuid.uuid4()}_{file.filename}"

                    path = f"company_requests/{new_request.id}/{unique_name}"

                    # 🔥 Subir a Firebase
                    blob = bucket.blob(path)

                    blob.upload_from_file(
                        file.file,
                        content_type=file.content_type
                    )

                    # 🔥 Guardar metadata en DB
                    request_file = RequestFile(
                        request_id=new_request.id,
                        file_name=file.filename,
                        file_path=path,
                        content_type=file.content_type,
                        size=size
                    )

                    db.add(request_file)

            db.commit()
            db.refresh(new_request)

            return new_request
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_request_id(db: Session, request_id): 
        request = db.query(RegisterRequest).filter(RegisterRequest.id == request_id).first()
        
        if request is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        return request
    
    @staticmethod
    def get_all_requests(db: Session):
        requests= db.query(RegisterRequest).order_by(desc(RegisterRequest.created_at)).all()

        if requests is None: 
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="There aren't requests yet."
            )
        
        if requests.count == 0:
            return "There aren't requests yet."
        
        return requests
    
    @staticmethod
    def reject_request(db: Session, request_id, data: RegisterRequestUpdate):

        request = db.query(RegisterRequest).filter(RegisterRequest.id == request_id).first()

        if request is None: 
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        
        company_exists = db.query(Company).filter(Company.nit == request.nit_company).first()

        if company_exists: 
            request.status = Status.REJECTED
            request.reason_for_rejection = "Company's nit already exists."

            db.commit()
            db.refresh(request)
        
            return request 
        
        request.status = data.status
        request.reason_for_rejection = data.reason_for_rejection

        db.commit()
        db.refresh(request)

        return request
    
    @staticmethod
    def approved_request(db: Session, request_id, background_task: BackgroundTasks):

        request = db.query(RegisterRequest).filter(RegisterRequest.id == request_id).first()

        if request is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request is not found")

        if request.status != Status.PENDING:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Request has already been processed.")

        if db.query(Company).filter(Company.nit == request.nit_company).first():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company's nit already exists.")

        try:
            company = Company(
                legal_name=request.legal_name_company,
                trade_name=request.trade_name_company,
                nit=request.nit_company,
                economic_activity=request.economic_activity,
                entity_type=request.entity_type,
                is_legally_constituted=request.is_legally_constituted
            )
            db.add(company)
            db.flush()

            created_users = []

            
            existing_rep = db.query(User).filter(User.email == request.rep_email).first()

            if existing_rep:
                db.add(UserCompany(user_id=existing_rep.id, company_id=company.id, role=CompanyRole.LEGAL_REPRESENTATIVE))
            else:
                rep_password = generate_secure_pass()
                rep_legal = User(
                    name=request.rep_name,
                    email=request.rep_email,
                    password_hash=hash_password(rep_password),
                    phone=request.rep_phone,
                    document_type=request.rep_document_type,
                    document_number=request.rep_document_number,
                )
                db.add(rep_legal)
                db.flush()
                db.add(UserCompany(user_id=rep_legal.id, company_id=company.id, role=CompanyRole.LEGAL_REPRESENTATIVE))
                created_users.append({"instance": rep_legal, "password": rep_password})

            # --- Usuarios adicionales ---
            for user_data in request.usuarios_json:
                existing_user = db.query(User).filter(User.email == user_data["email"]).first()

                if existing_user:
                    db.add(UserCompany(user_id=existing_user.id, company_id=company.id, role=CompanyRole.USER))
                    continue 

                password = generate_secure_pass()
                user = User(
                    name=user_data["name"],
                    email=user_data["email"],
                    password_hash=hash_password(password),
                    document_type=user_data["document_type"],
                    document_number=user_data["document_number"]
                )
                db.add(user)
                db.flush()
                db.add(UserCompany(user_id=user.id, company_id=company.id, role=CompanyRole.USER))
                created_users.append({"instance": user, "password": password})

            request.status = Status.APPROVED
            db.commit()

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

        # Enviar emails a todos los usuarios nuevos
        for u in created_users:
            background_task.add_task(
                EmailService.send_activation_email,
                    u["instance"].email,
                    u["instance"].document_number,
                    u["password"],
                    create_activation_token(u["instance"].id)
            )
            print("correo enviado a:", u["instance"].email)
        return request
            
    


        

    
        
        
        
