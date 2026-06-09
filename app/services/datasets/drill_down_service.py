from datetime import date

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.dimensions.dim_category import DimCategory
from app.models.dimensions.dim_client import DimClient
from app.models.dimensions.dim_date import DimDate
from app.models.dimensions.dim_payment import DimPayment
from app.models.dimensions.dim_product import DimProduct
from app.models.dimensions.dim_supplier import DimSupplier
from app.models.fact.fact_operation import FactOperation
from app.services.datasets.run_etl import OPERATION_TYPE_MAP


class DrillDownService: 

    @staticmethod
    def calculate_drilldown(
        db: Session,
        company_id: int,
        dimension: str,
        fecha_inicio: date,
        fecha_fin: date,
        operation_type: str = None,
    ) -> dict:
        
        DRILLDOWN_DIMENSIONS = {"product", "category", "client", "supplier", "payment"}
        if dimension not in DRILLDOWN_DIMENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Dimensión no válida. Opciones: {', '.join(DRILLDOWN_DIMENSIONS)}"
            )

        # Mapear dimensión a modelo y campo nombre
        dim_map = {
            "product":  (DimProduct,  DimProduct.name,  FactOperation.dim_product_id),
            "category": (DimCategory, DimCategory.name, FactOperation.dim_category_id),
            "client":   (DimClient,   DimClient.name,   FactOperation.dim_client_id),
            "supplier": (DimSupplier, DimSupplier.name, FactOperation.dim_supplier_id),
            "payment":  (DimPayment,  DimPayment.type,  FactOperation.dim_payment_id),
        }

        dim_model, dim_name_col, fact_fk_col = dim_map[dimension]

        # Query base
        query = db.query(
            dim_name_col.label("name"),
            FactOperation.operation_type,
            func.sum(FactOperation.total_amount).label("total"),
            func.count(FactOperation.id).label("transacciones"),
        ).join(
            DimDate, FactOperation.dim_date_id == DimDate.id
        ).join(
            dim_model, fact_fk_col == dim_model.id
        ).filter(
            FactOperation.company_id == company_id,
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin,
            fact_fk_col.isnot(None),
        )

        # Filtro opcional por tipo de operación
        if operation_type:
            op = OPERATION_TYPE_MAP.get(operation_type.strip().lower())
            if not op:
                raise HTTPException(status_code=400, detail=f"operation_type '{operation_type}' no reconocido.")
            query = query.filter(FactOperation.operation_type == op)

        results = query.group_by(dim_name_col, FactOperation.operation_type).all()

        if not results:
            return {
                "dimension": dimension,
                "period": {"fecha_inicio": str(fecha_inicio), "fecha_fin": str(fecha_fin)},
                "data": [],
                "message": "No hay información adicional disponible para este elemento."
            }

        # Agrupar por nombre de dimensión
        grouped = {}
        for row in results:
            if row.name not in grouped:
                grouped[row.name] = {
                    "name": row.name,
                    "total": 0,
                    "transacciones": 0,
                    "breakdown": {}
                }
            grouped[row.name]["total"] += float(row.total)
            grouped[row.name]["transacciones"] += row.transacciones
            grouped[row.name]["breakdown"][row.operation_type] = float(row.total)

        # Ordenar por total descendente
        data = sorted(grouped.values(), key=lambda x: x["total"], reverse=True)

        return {
            "dimension": dimension,
            "period": {
                "fecha_inicio": str(fecha_inicio),
                "fecha_fin": str(fecha_fin)
            },
            "data": data,
        }
    
    @staticmethod
    def get_dimension_detail(
        db: Session,
        company_id: int,
        dimension: str,
        name: str,
        fecha_inicio: date,
        fecha_fin: date,
        granularity: str = "day",
    ) -> dict:

        VALID_GRANULARITIES = {"day", "week", "month"}
        if granularity not in VALID_GRANULARITIES:
            raise HTTPException(status_code=400, detail=f"Granularidad no válida. Opciones: day, week, month")

        dim_map = {
            "product":  (DimProduct,  DimProduct.name,  FactOperation.dim_product_id),
            "category": (DimCategory, DimCategory.name, FactOperation.dim_category_id),
            "client":   (DimClient,   DimClient.name,   FactOperation.dim_client_id),
            "supplier": (DimSupplier, DimSupplier.name, FactOperation.dim_supplier_id),
            "payment":  (DimPayment,  DimPayment.type,  FactOperation.dim_payment_id),
        }

        if dimension not in dim_map:
            raise HTTPException(status_code=400, detail=f"Dimensión no válida.")

        dim_model, dim_name_col, fact_fk_col = dim_map[dimension]

        # ── Filtro base ─────────────────────────────────────────────
        base_filter = [
            FactOperation.company_id == company_id,
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin,
            dim_name_col == name.strip().lower(),
        ]

        base_query = db.query(FactOperation).join(
            DimDate, FactOperation.dim_date_id == DimDate.id
        ).join(
            dim_model, fact_fk_col == dim_model.id
        ).filter(*base_filter)

        # ── 1. Breakdown por tipo de operación ──────────────────────
        breakdown_rows = db.query(
            FactOperation.operation_type,
            func.sum(FactOperation.total_amount).label("total"),
            func.count(FactOperation.id).label("transacciones"),
        ).join(
            DimDate, FactOperation.dim_date_id == DimDate.id
        ).join(
            dim_model, fact_fk_col == dim_model.id
        ).filter(*base_filter).group_by(FactOperation.operation_type).all()

        breakdown = {
            "venta": None,
            "compra": None,
            "costo": None,
        }
        op_reverse = {v: k for k, v in OPERATION_TYPE_MAP.items()}
        for row in breakdown_rows:
            key = op_reverse.get(row.operation_type)
            if key:
                breakdown[key] = float(row.total)

        # ── 2. Margen de utilidad (solo productos) ──────────────────
        margen_utilidad = None

        if dimension == "product":
            ventas = breakdown.get("venta")
            compras = breakdown.get("compra")

            if ventas is not None and ventas > 0:
                if compras is not None:
                    margen_utilidad = round(((ventas - compras) / ventas) * 100, 2)
                else:
                    # no hay costos → margen inflado
                    margen_utilidad = 100.0

        # ── 3. Evolución en el tiempo ───────────────────────────────
        if granularity == "day":
            period_col = DimDate.full_date
            period_label = func.cast(DimDate.full_date, db.bind.dialect.colspecs.get(type(DimDate.full_date), None) if db.bind else None)
        elif granularity == "week":
            period_col = func.date_trunc("week", DimDate.full_date)
        else:
            period_col = func.date_trunc("month", DimDate.full_date)

        evolucion_rows = db.query(
            period_col.label("periodo"),
            FactOperation.operation_type,
            func.sum(FactOperation.total_amount).label("total"),
        ).join(
            DimDate, FactOperation.dim_date_id == DimDate.id
        ).join(
            dim_model, fact_fk_col == dim_model.id
        ).filter(*base_filter).group_by("periodo", FactOperation.operation_type).order_by("periodo").all()

        # Agrupar evolución por periodo
        evolucion_grouped = {}
        for row in evolucion_rows:
            periodo_str = str(row.periodo)[:10]
            if periodo_str not in evolucion_grouped:
                evolucion_grouped[periodo_str] = {"periodo": periodo_str}
            key = op_reverse.get(row.operation_type, str(row.operation_type))
            evolucion_grouped[periodo_str][key] = float(row.total)

        evolucion = list(evolucion_grouped.values())

        # ── 4. Registros completos del RawRecord ────────────────────
        fact_ids = [f.id for f in base_query.all()]
        registros = []
        if fact_ids:
            from app.models.dataset.raw_record import RawRecord
            raw_records = db.query(RawRecord).join(
                FactOperation, RawRecord.id == FactOperation.raw_record_id
            ).filter(FactOperation.id.in_(fact_ids)).all()
            registros = [r.row_payload for r in raw_records]

        return {
            "dimension": dimension,
            "name": name,
            "period": {
                "fecha_inicio": str(fecha_inicio),
                "fecha_fin": str(fecha_fin),
                "granularity": granularity,
            },
            "breakdown": breakdown,
            "margen_utilidad_pct": margen_utilidad,
            "evolucion": evolucion,
            "registros": registros,
        }