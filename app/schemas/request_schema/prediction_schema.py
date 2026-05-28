from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ForecastHorizon(str, Enum):
    ONE_MONTH    = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS   = "6m"
    ONE_YEAR     = "1y"


class PredictionRequest(BaseModel):
    horizon: ForecastHorizon = Field(
        default=ForecastHorizon.ONE_MONTH,
        description="Horizonte de predicción desde hoy"
    )


class ForecastPoint(BaseModel):
    date: str
    value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class VariableForecast(BaseModel):
    variable: str                        # "sale" | "purchase" | "expense"
    model_order: str                     # "(p,d,q)"
    historical: list[ForecastPoint]
    forecast: list[ForecastPoint]