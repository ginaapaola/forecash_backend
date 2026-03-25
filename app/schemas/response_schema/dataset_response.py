from pydantic import BaseModel
from datetime import datetime


class DatasetUploadResponse(BaseModel):
    raw_dataset_id: int
    status:         str
    etl_summary:    dict
    warnings:       list[str]


class DatasetListResponse(BaseModel):
    id:             int
    file_name:      str
    file_type:      str
    status:         str
    arima_ready:    bool
    etl_summary:    dict | None
    created_at:     datetime

    model_config = {"from_attributes": True}