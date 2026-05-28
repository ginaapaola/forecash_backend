from app.core.db.database import SessionLocal
from app.models.dimensions.operation_type import OperationType
from app.services.forecasting.prediction_service import get_daily_series, get_monthly_series
from app.models.dimensions.dim_date import DimDate
from app.models.dimensions.dim_category import DimCategory
from app.models.dimensions.dim_client import DimClient
from app.models.dimensions.dim_payment import DimPayment
from app.models.dimensions.dim_product import DimProduct
from app.models.dimensions.dim_supplier import DimSupplier
from app.models.fact.fact_operation import FactOperation


db = SessionLocal()

try: 
    print("\n=== DAILY SERIES ===\n")

    daily_rows = get_daily_series(
        db=db,
        company_id=7,
        operation_type=OperationType.sale,
        days=30,
    )

    for row in daily_rows:
        print(row)

    print("\n=== MONTHLY SERIES ===\n")

    monthly_rows = get_monthly_series(
        db=db,
        company_id=7,
        operation_type=OperationType.sale,
        months=2
    )

    for row in monthly_rows:
        print(row)

finally: 
    db.close()

