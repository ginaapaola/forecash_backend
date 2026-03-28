from datetime import date

from fastapi import HTTPException
from sqlalchemy import Integer, String, func, case
from sqlalchemy.orm import Session

from app.models.dimensions.dim_category import DimCategory
from app.models.dimensions.dim_date import DimDate
from app.models.dimensions.dim_payment import DimPayment
from app.models.dimensions.dim_product import DimProduct
from app.models.dimensions.dim_supplier import DimSupplier
from app.models.dimensions.operation_type import OperationType
from app.models.fact.fact_operation import FactOperation

from collections import defaultdict

def _get_time_series(db, company_id, fecha_inicio, fecha_fin, operation_type=None):
    
    # Inferir granularidad según el rango de fechas
    delta = (fecha_fin - fecha_inicio).days

    if delta <= 31:
        period = DimDate.full_date
    elif delta <= 90:
        period = func.date_trunc('week', DimDate.full_date)
    elif delta <= 180:
        period = func.concat(
            func.date_part('year', DimDate.full_date).cast(Integer), '-',
            func.lpad(func.date_part('month', DimDate.full_date).cast(String), 2, '0'), '-Q',
            case(
                (func.extract('day', DimDate.full_date) <= 15, '1'),
                else_='2'
            )
        )
    else:
        period = func.date_trunc('month', DimDate.full_date)

    query = db.query(
        period.label("period"),
        FactOperation.operation_type,
        func.sum(FactOperation.total_amount).label("total")
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).filter(
        FactOperation.company_id == company_id,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    )

    if operation_type:
        query = query.filter(FactOperation.operation_type == operation_type)

    rows = query.group_by(period, FactOperation.operation_type).order_by(period).all()

    chart_map = defaultdict(lambda: {"ventas": None, "compras": None, "gastos": None})
    for row in rows:
        key = str(row.period)[:10]
        if row.operation_type == OperationType.sale:
            chart_map[key]["ventas"] = float(row.total)
        elif row.operation_type == OperationType.purchase:
            chart_map[key]["compras"] = float(row.total)
        elif row.operation_type == OperationType.expense:
            chart_map[key]["gastos"] = float(row.total)

    return {
        "granularity": "daily" if delta <= 7 else "weekly" if delta <= 30 else "monthly" ,
        "data": [{"period": k, **v} for k, v in sorted(chart_map.items())]
    }


@staticmethod
def calculate_metrics_by_period(
    db: Session,
    company_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    ) -> dict:

    from sqlalchemy import func

    base_query = db.query(
        FactOperation.operation_type,
        func.sum(FactOperation.total_amount).label("total")
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).filter(
        FactOperation.company_id == company_id,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(FactOperation.operation_type).all()

    totals = {row.operation_type: float(row.total) for row in base_query}

    total_ventas = totals.get(OperationType.sale)
    total_compras = totals.get(OperationType.purchase)
    total_costos = totals.get(OperationType.expense)

    total_egresos = None
    if total_compras is not None and total_costos is not None:
        total_egresos = total_compras + total_costos
    elif total_compras is not None:
        total_egresos = total_compras
    elif total_costos is not None:
        total_egresos = total_costos

    utilidad_bruta = None
    if total_ventas is not None and total_compras is not None:
        utilidad_bruta = total_ventas - total_compras

    utilidad_neta = None
    if total_ventas is not None and total_egresos is not None:
        utilidad_neta = total_ventas - total_egresos

    margen_ganancia = None
    if utilidad_neta is not None and total_ventas and total_ventas > 0:
        margen_ganancia = round(utilidad_neta / total_ventas * 100, 2)

    total_transacciones = db.query(func.count(FactOperation.id)).filter(
        FactOperation.company_id == company_id,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).join(DimDate, FactOperation.dim_date_id == DimDate.id).scalar()

    ticket_promedio = None
    if total_ventas is not None:
        total_ventas_count = db.query(func.count(FactOperation.id)).join(
            DimDate, FactOperation.dim_date_id == DimDate.id
        ).filter(
            FactOperation.company_id == company_id,
            FactOperation.operation_type == OperationType.sale,
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin
        ).scalar()
        if total_ventas_count and total_ventas_count > 0:
            ticket_promedio = round(total_ventas / total_ventas_count, 2)
    
    # =====================
    # INSIGHTS
    # =====================

    top_producto = db.query(
        DimProduct.name,
        func.sum(FactOperation.quantity)
    ).join(
        DimProduct, FactOperation.dim_product_id == DimProduct.id
    ).join(DimDate, FactOperation.dim_date_id == DimDate.id).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.sale,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        DimProduct.name
    ).order_by(
        func.sum(FactOperation.quantity).desc()
    ).first()


    top_proveedor = db.query(
        DimSupplier.name,
        func.sum(FactOperation.quantity)
    ).join(
        DimSupplier, FactOperation.dim_supplier_id == DimSupplier.id
    ).join(DimDate, FactOperation.dim_date_id == DimDate.id).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.purchase,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        DimSupplier.name
    ).order_by(
        func.sum(FactOperation.quantity).desc()
    ).first()


    top_gasto = db.query(
        DimCategory.name,
        func.count(FactOperation.id)
    ).join(
        DimCategory, FactOperation.dim_category_id == DimCategory.id
    ).join(DimDate, FactOperation.dim_date_id == DimDate.id).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.expense,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        DimCategory.name
    ).order_by(
        func.count(FactOperation.id).desc()
    ).first()

    available_metrics = []
    if total_ventas is not None:
        available_metrics.append("ventas")
    if total_compras is not None:
        available_metrics.append("compras")
    if total_costos is not None:
        available_metrics.append("costos")
    if utilidad_neta is not None:
        available_metrics.append("utilidad")
    if margen_ganancia is not None:
        available_metrics.append("margen")
    
    chart = _get_time_series(
        db,
        company_id,
        fecha_inicio,
        fecha_fin
    )

    return {
       "period": {
            "fecha_inicio": str(fecha_inicio),
            "fecha_fin": str(fecha_fin),
        },
        "available_metrics": available_metrics,
        "kpis": {
            "total_ventas": total_ventas,
            "total_compras": total_compras,
            "total_costos": total_costos,
            "total_egresos": total_egresos,
            "utilidad_bruta": utilidad_bruta,
            "utilidad_neta": utilidad_neta,
            "margen_ganancia_pct": margen_ganancia,
            "ticket_promedio": ticket_promedio,
            "total_transacciones": total_transacciones,
        },
        "insights": {
            "top_producto": top_producto[0] if top_producto else None,
            "top_proveedor": top_proveedor[0] if top_proveedor else None,
            "top_gasto": top_gasto[0] if top_gasto else None
        },

        "chart": chart
    }

def get_operation_breakdown(
    db: Session,
    company_id: int,
    operation_type: OperationType,
    fecha_inicio: date,
    fecha_fin: date,
):
    distribution = db.query(
        func.coalesce(DimProduct.name, DimCategory.name).label("name"),
        func.sum(FactOperation.total_amount).label("total"),
        func.sum(FactOperation.quantity).label("quantity")
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).outerjoin(   # 👈 clave
        DimProduct, FactOperation.dim_product_id == DimProduct.id
    ).outerjoin(   # 👈 clave
        DimCategory, FactOperation.dim_category_id == DimCategory.id
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == operation_type,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        func.coalesce(DimProduct.name, DimCategory.name)
    ).all()

    payment_methods = db.query(
        DimPayment.type.label("payment_method"),
        func.sum(FactOperation.total_amount).label("total")
    ).select_from(FactOperation).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).outerjoin(
        DimPayment, FactOperation.dim_payment_id == DimPayment.id
    ). filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == operation_type,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ). group_by(
        DimPayment.type
    )

    chart = _get_time_series(
        db,
        company_id,
        fecha_inicio,
        fecha_fin,
        operation_type
    )

    utility_per_unit = get_utility_per_unit(
        db,
        company_id,
        fecha_inicio,
        fecha_fin
    )

    return {
        "distribution": [
            {
                "name": row[0],
                "value": float(row[1]),
                "quantity": float(row.quantity)
            }
            for row in distribution
        ],
        "payment_methods" : [
            {
                "method": row.payment_method,
                "total": float(row.total)
            }
            for row in payment_methods
        ],
        "chart": chart,
        "utility": utility_per_unit
    }


def get_utility_per_unit(
    db: Session,
    company_id: int,
    fecha_inicio: date,
    fecha_fin: date,
):
    
    # Subquery: precio de venta promedio por producto (en el período)
    ventas = db.query(
        DimProduct.id.label("product_id"),
        DimProduct.name.label("name"),
        func.avg(FactOperation.unit_price).label("avg_sale_price"),
        func.sum(FactOperation.quantity).label("total_quantity_sold")
    ).join(
        DimProduct, FactOperation.dim_product_id == DimProduct.id
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.sale,
        FactOperation.unit_price.isnot(None),
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        DimProduct.id, DimProduct.name
    ).subquery()

    # Subquery: costo histórico promedio por producto (SIN restricción de fechas)
    costo_historico = db.query(
        DimProduct.id.label("product_id"),
        func.avg(FactOperation.unit_price).label("avg_cost")
    ).join(
        DimProduct, FactOperation.dim_product_id == DimProduct.id
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.purchase,
        FactOperation.unit_price.isnot(None),
    ).group_by(
        DimProduct.id
    ).subquery()

    # outerjoin para incluir productos aunque no tengan compras registradas
    results = db.query(
        ventas.c.name,
        ventas.c.avg_sale_price,
        costo_historico.c.avg_cost,
        ventas.c.total_quantity_sold,
        (ventas.c.avg_sale_price - func.coalesce(costo_historico.c.avg_cost, 0)).label("utility_per_unit")
    ).outerjoin(
        costo_historico, ventas.c.product_id == costo_historico.c.product_id
    ).order_by(
        (ventas.c.avg_sale_price - func.coalesce(costo_historico.c.avg_cost, 0)).desc()
    ).all()

    return [
        {
            "name": row.name,
            "avg_sale_price": float(row.avg_sale_price) if row.avg_sale_price else 0,
            "avg_cost": float(row.avg_cost) if row.avg_cost else 0,
            "quantity_sold": float(row.total_quantity_sold),
            "utility_per_unit": float(row.utility_per_unit)
        }
        for row in results
    ]