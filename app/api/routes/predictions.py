from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db.session import get_db

from app.dependencies.get_company import get_company
from app.models.dimensions.operation_type import OperationType

from app.schemas.request_schema.prediction_schema import (
    PredictionRequest,
    VariableForecast,
)

from app.schemas.response_schema.prediction_response import (
    PredictionResponse,
)

from app.services.forecasting.prediction_service import (
    HORIZON_CONFIG,
    generate_forecast,
)

router = APIRouter(
    prefix="/predictions",
    tags=["Predictions"],
)

VARIABLES = [
    ("sale", OperationType.sale),
    ("purchase", OperationType.purchase),
    ("expense", OperationType.expense),
]


@router.post("/", response_model=PredictionResponse)
def generate_predictions(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    company: dict = Depends(get_company)
):

    company_id = company["company"].id

    predictions = []

    for variable_name, operation_type in VARIABLES:

        try:

            result = generate_forecast(
                db=db,
                company_id=company_id,
                operation_type=operation_type,
                horizon=request.horizon,
            )

            predictions.append(
                VariableForecast(
                    variable=variable_name,
                    model_order=result["model_order"],
                    historical=result["historical"],
                    forecast=result["forecast"],
                )
            )

        except ValueError:
            # No suficientes datos
            continue

        except Exception as e:
            import traceback
            print(f"\nERROR EN {variable_name} con horizon {request.horizon}:")
            traceback.print_exc()
            continue

    return PredictionResponse(
        horizon=request.horizon,
        forecast_days=HORIZON_CONFIG[request.horizon]["forecast_periods"],
        predictions=predictions,
    )