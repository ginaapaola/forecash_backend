from pydantic import BaseModel

from app.schemas.request_schema.prediction_schema import VariableForecast


class PredictionResponse(BaseModel):
    horizon: str
    forecast_days: int
    predictions: list[VariableForecast]  # siempre 3 elementos