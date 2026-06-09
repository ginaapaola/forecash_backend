from typing import Optional
from pydantic import BaseModel, model_validator

from app.models.company.regime_type import RegimeType


class TaxConfiguration(BaseModel):
    regime_type: Optional[RegimeType] = RegimeType.NONE
    tax_rate: Optional[float] = None
    is_vat_responsible: Optional[bool] = None

    @model_validator(mode='after')
    def validate_tax_config(self):
        if self.regime_type != RegimeType.NONE:
            if self.tax_rate is None:
                raise ValueError("tax_rate is required when regime_type is defined")
            if self.tax_rate < 0 or self.tax_rate > 100:
                raise ValueError("tax_rate must be between 0 and 100")
            if self.is_vat_responsible is None:
                raise ValueError("is_vat_responsible is required when regime_type is defined")
        return self