from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.db.base import Base
from app.models.company.entity_type import EntityType
from app.models.request.request_status import Status
from app.models.user.doc_type import UserDocType


class RegisterRequest(Base):
    __tablename__ = "requests"

    #ID DE LA REQUEST

    id = Column(Integer, primary_key=True, index=True)

    #INFORMACIÓN DEL REPRESENTANTE

    rep_name = Column(String, nullable=False)
    rep_email = Column(String, unique=True, nullable=False, index=True)
    rep_phone = Column(String, unique=True, nullable=False)
    rep_document_type = Column(
        Enum(UserDocType, name="document_type"),
        nullable=False
    )
    rep_document_number = Column(String, unique=True, nullable=False)

    # INFORMACIÓN DE LA EMPRESA 

    legal_name_company = Column(String, nullable=False)
    trade_name_company = Column(String, nullable=False)
    nit_company = Column(String, unique=True, nullable=False, index=True)
    economic_activity = Column(String, nullable=False)
    entity_type = Column(
        Enum(EntityType, name='entity_type'),
        nullable=False
    )
    is_legally_constituted = Column(Boolean, nullable=False)

    #Usuarios adicionales (SI LOS HAY)
    usuarios_json = Column(JSON, nullable=True)

    #ESTADO (POR DEFECTO ES PENDIENTE)

    status = Column(
        Enum(Status, name="status"),
        nullable= False,
        default=Status.PENDING
    )

    #ESTA COLUMNA SÓLO SE LLENA CUANDO SE ACTUALIZA EL ESTADO DE UNA REQUEST (RECHAZADO) PARA CONOCER EL MOTIVO DE SU RECHAZO.
    reason_for_rejection = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    files = relationship(
        "RequestFile",
        backref="requests",
        cascade="all, delete-orphan"
    )