from typing import List
import uuid

from fastapi import HTTPException, UploadFile, status
import json
from sqlalchemy.orm import Session

from app.core.firebase.firebase_config import bucket
from app.models.company.company import Company
from app.models.request.file import RequestFile
from app.models.request.register_request import RegisterRequest
from app.models.request.request_status import Status
from app.models.user.user import User
from app.schemas.request_schema.register_request import CompanyRequestCreate, RegisterRequestUpdate

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
        requests= db.query(RegisterRequest)

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


        

    
        
        
        
