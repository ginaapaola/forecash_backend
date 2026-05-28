from datetime import date, timedelta

import pandas as pd
from pmdarima import auto_arima
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.dimensions.dim_date import DimDate
from app.models.dimensions.operation_type import OperationType
from app.models.fact.fact_operation import FactOperation


HORIZON_CONFIG = {
    "1m": {
        "frequency": "monthly",
        "forecast_periods": 1,
        "history_months": 15,
        "seasonal": False,
    },

    "3m": {
        "frequency": "monthly",
        "forecast_periods": 3,
        "history_months": 24,
        "seasonal": False,
    },

    "6m": {
        "frequency": "monthly",
        "forecast_periods": 6,
        "history_months": 30,
        "seasonal": False,
    },

    "1y": {
        "frequency": "monthly",
        "forecast_periods": 12,
        "history_months": 36,
        "seasonal": True,
    },
}


# =========================================================
# MONTHLY SERIES
# =========================================================

def get_monthly_series(
    db: Session,
    company_id: int,
    operation_type: OperationType,
    months: int = 12,
):
    today = date.today()

    current_period = today.year * 100 + today.month

    stmt = (
        select(
            DimDate.year,
            DimDate.month,
            func.sum(FactOperation.total_amount).label("total"),
        )
        .join(FactOperation, FactOperation.dim_date_id == DimDate.id)
        .where(
            FactOperation.company_id == company_id,
            FactOperation.operation_type == operation_type,
            (DimDate.year * 100 + DimDate.month) < current_period,
        )
        .group_by(
            DimDate.year,
            DimDate.month,
        )
        .order_by(
            DimDate.year.desc(),
            DimDate.month.desc(),
        )
        .limit(months)
    )

    result = db.execute(stmt)

    return result.all()


def build_monthly_series(rows: list) -> pd.Series:

    if not rows:
        raise ValueError("No hay datos mensuales.")
    
    print(f"Rows recibidos: {len(rows)}")
    print(f"Primer row: {rows[0]}")
    print(f"Último row: {rows[-1]}")

    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    # ... resto del código

    rows = sorted(rows, key=lambda r: (r[0], r[1]))

    series = pd.Series(
        data=[float(r[2]) for r in rows],
        index=pd.to_datetime([
            date(r[0], r[1], 1)
            for r in rows
        ]),
        name="value",
    )

    full_index = pd.date_range(
        start=series.index.min(),
        end=series.index.max(),
        freq="MS",
    )

    series = series.reindex(full_index)

    series = series.ffill().bfill()

    print(f"Largo serie: {len(series)}")
    print(f"Únicos: {series.nunique()}")
    print(f"Serie:\n{series}")

    if len(series) < 12:
        raise ValueError(
            "No hay suficientes datos mensuales."
        )

    if series.nunique() < 6:
        raise ValueError(
            "La serie mensual no tiene suficiente variabilidad."
        )

    return series


# =========================================================
# MODEL TRAINING
# =========================================================

def train_arima_model(
    series: pd.Series,
    seasonal: bool,
):

    try:

        model = auto_arima(
            series,

            seasonal=seasonal,

            m=12 if seasonal else 1,

            start_p=1,
            start_q=1,

            max_p=3,
            max_q=3,

            max_d=2,

            stepwise=True,

            suppress_warnings=True,

            error_action="ignore",

            trace=True,

            information_criterion="aic",
        )

        return model

    except Exception as e:

        print("\nERROR TRAINING MODEL:")
        print(str(e))

        raise ValueError(
            "No fue posible entrenar el modelo"
        )


# =========================================================
# FORECAST RESPONSE
# =========================================================

def build_forecast_response(
    series: pd.Series,
    model,
    forecast_periods: int,
    frequency: str,
):

    forecast_values, conf_int = model.predict(
        n_periods=forecast_periods,
        return_conf_int=True,
        alpha=0.05,
    )

    today = date.today()

    # ============================================
    # FUTURE DATES
    # ============================================

    if frequency == "daily":

        future_dates = [
            today + timedelta(days=i)
            for i in range(forecast_periods)
        ]

    else:

        future_dates = []

        year = today.year
        month = today.month

        for i in range(forecast_periods):

            if i > 0:
                month += 1

                if month > 12:
                    month = 1
                    year += 1

            future_dates.append(
                date(year, month, 1)
            )

    # ============================================
    # HISTORICAL
    # ============================================

    historical = [
        {
            "date": str(d.date()),
            "value": round(max(0, float(v)), 2),
        }
        for d, v in series.items()
    ]

    # ============================================
    # FORECAST
    # ============================================

    forecast = []

    for i in range(forecast_periods):

        predicted = max(0, float(forecast_values[i]))

        lower = max(0, float(conf_int[i][0]))

        upper = max(0, float(conf_int[i][1]))

        forecast.append({
            "date": str(future_dates[i]),
            "value": round(predicted, 2),
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2),
        })

    return {
        "model_order": str(model.order),
        "seasonal_order": str(model.seasonal_order),
        "historical": historical,
        "forecast": forecast,
    }


# =========================================================
# MAIN FORECAST
# =========================================================

def generate_forecast(
    db: Session,
    company_id: int,
    operation_type: OperationType,
    horizon: str,
):
    config = HORIZON_CONFIG[horizon]

    rows = get_monthly_series(
        db=db,
        company_id=company_id,
        operation_type=operation_type,
        months=config["history_months"],
    )

    series = build_monthly_series(rows)

    model = train_arima_model(
        series=series,
        seasonal=config["seasonal"],
    )

    return build_forecast_response(
        series=series,
        model=model,
        forecast_periods=config["forecast_periods"],
        frequency="monthly",
    )