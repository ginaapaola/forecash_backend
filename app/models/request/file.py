from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.db.base import Base


class RequestFile(Base):
    __tablename__ = "request_files"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(
        Integer, 
        ForeignKey("requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
        )
    #RUTA EN FIREBASE 
    file_path = Column(String, nullable=False)
    
    #INFORMACIÓN DEL ARCHIVO (METADATOS)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    content_type = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())