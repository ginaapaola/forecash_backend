"""Consultas agregadas para metricas y tableros financieros.

Calcula KPIs, series temporales, distribuciones, evolucion de productos,
categorias y gastos a partir del modelo dimensional de operaciones.
"""

from datetime import date

from fastapi import HTTPException
from sqlalchemy import Integer, String, cast, func, case
from sqlalchemy.orm import Session

from app.models.dataset.raw_record import RawRecord
from app.models.dimensions.dim_category import DimCategory
from app.models.dimensions.dim_date import DimDate
from app.models.dimensions.dim_payment import DimPayment
from app.models.dimensions.dim_product import DimProduct
from app.models.dimensions.dim_supplier import DimSupplier
from app.models.dimensions.operation_type import OperationType
from app.models.fact.fact_operation import FactOperation

from collections import defaultdict

group_key = func.coalesce(
    cast(FactOperation.dim_product_id, String),
    func.nullif(FactOperation.concept, "")
)

name_expr = func.coalesce(
    DimProduct.name,
    func.nullif(FactOperation.concept, ""),
    "Sin nombre"
)

amount_expr = func.coalesce(
    func.nullif(FactOperation.subtotal, 0),
    FactOperation.total_amount
)


def _get_time_series(db, company_id, fecha_inicio, fecha_fin, operation_type=None):
    """Construye una serie temporal con granularidad dinamica por rango."""

    delta = (fecha_fin - fecha_inicio).days

    # 🎯 Definir granularidad real
    if delta <= 31:
        granularity = "daily"
        period = func.date_trunc('day', DimDate.full_date)
    elif delta <= 90:
        granularity = "weekly"
        period = func.date_trunc('week', DimDate.full_date)
    elif delta <= 365:
        granularity = "monthly"
        period = func.date_trunc('month', DimDate.full_date)
    else:
        granularity = "yearly"
        period = func.date_trunc('year', DimDate.full_date)

    query = db.query(
        period.label("period"),
        FactOperation.operation_type,
        func.sum(amount_expr).label("total")
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).filter(
        FactOperation.company_id == company_id,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    )

    if operation_type:
        query = query.filter(FactOperation.operation_type == operation_type)

    rows = query.group_by(period, FactOperation.operation_type)\
                .order_by(period)\
                .all()

    chart_map = defaultdict(lambda: {"ventas": 0, "compras": 0, "gastos": 0})

    for row in rows:
        key = row.period.strftime("%Y-%m-%d")  # ✅ fecha válida SIEMPRE

        if row.operation_type == OperationType.sale:
            chart_map[key]["ventas"] = float(row.total)
        elif row.operation_type == OperationType.purchase:
            chart_map[key]["compras"] = float(row.total)
        elif row.operation_type == OperationType.expense:
            chart_map[key]["gastos"] = float(row.total)

    return {
        "granularity": granularity,
        "data": [
            {"period": k, **v}
            for k, v in sorted(chart_map.items())
        ]
    }


@staticmethod
def calculate_metrics_by_period(
    db: Session,
    company_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    ) -> dict:
    """Calcula KPIs, insights y datos de graficas para un periodo."""

    from sqlalchemy import func

    base_query = db.query(
        FactOperation.operation_type,
        func.sum(amount_expr).label("total")
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

    utilidad_operativa = None
    if total_ventas is not None and total_egresos is not None:
        utilidad_operativa = total_ventas - total_egresos

    margen_ganancia = None
    if utilidad_operativa is not None and total_ventas and total_ventas > 0:
        margen_ganancia = round(utilidad_operativa / total_ventas * 100, 2)

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
        func.coalesce(
            DimProduct.name,
            func.nullif(FactOperation.concept, "")   # 🔥 evita strings vacíos
        ).label("name"),

        func.sum(FactOperation.quantity).label("quantity")

    ).outerjoin(
        DimProduct, FactOperation.dim_product_id == DimProduct.id

    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id

    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.sale,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin

    ).group_by(
        func.coalesce(
            DimProduct.name,
            func.nullif(FactOperation.concept, "")
        )
    ).order_by(
        func.sum(FactOperation.quantity).desc()
    ).first()


    top_proveedor = db.query(
        func.coalesce(
            DimSupplier.name,
            func.nullif(FactOperation.concept, "")
        ).label("name"),
        func.sum(FactOperation.quantity)
    ).outerjoin(
        DimSupplier, FactOperation.dim_supplier_id == DimSupplier.id
    ).join(DimDate, FactOperation.dim_date_id == DimDate.id).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.purchase,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        func.coalesce(
            DimSupplier.name,
            func.nullif(FactOperation.concept, "")
        )
    ).order_by(
        func.sum(FactOperation.quantity).desc()
    ).first()


    top_gasto = db.query(
        func.coalesce(
            DimCategory.name,
            func.nullif(FactOperation.concept, "")
        ).label("name"),
        func.count(FactOperation.id)
    ).outerjoin(
        DimCategory, FactOperation.dim_category_id == DimCategory.id
    ).join(DimDate, FactOperation.dim_date_id == DimDate.id).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.expense,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        func.coalesce(
            DimCategory.name,
            func.nullif(FactOperation.concept, "")
        )
    ).order_by(
        func.count(FactOperation.id).desc()
    ).first()

    categories = db.query(
        DimCategory.id.label("id"),
        DimCategory.name.label("name"),
        func.sum(amount_expr).label("total"),
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).outerjoin(
        DimCategory, FactOperation.dim_category_id == DimCategory.id
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.sale,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        DimCategory.id,
        DimCategory.name
    ).all()

    total_sum = sum(row.total for row in categories)

    categories_data = [
        {
            "id": row.id,
            "name": row.name,
            "value": float(row.total),
            "percentage": round((row.total / total_sum) * 100, 2) if total_sum else 0
        }
        for row in categories
    ]


    available_metrics = []
    if total_ventas is not None:
        available_metrics.append("ventas")
    if total_compras is not None:
        available_metrics.append("compras")
    if total_costos is not None:
        available_metrics.append("costos")
    if utilidad_bruta is not None:
        available_metrics.append("utilidad_bruta")
    if utilidad_operativa is not None:
        available_metrics.append("utilidad_operativa")
    if margen_ganancia is not None:
        available_metrics.append("margen")
    
    chart = _get_time_series(
        db,
        company_id,
        fecha_inicio,
        fecha_fin
    )

    # ── PRODUCTOS: tabla + evolución ──────────────────────────────────────────
    # Reutiliza las mismas subqueries de get_products_summary pero embebidas
    # aquí para no abrir una segunda conexión ni duplicar el filtro de fechas.
 
    ventas_sq = (
        db.query(
            DimProduct.id.label("product_id"),
            group_key.label("group_key"),
            name_expr.label("name"),

            # 💰 precio promedio ponderado de venta
            (
                func.sum(FactOperation.unit_price * FactOperation.quantity) /
                func.nullif(func.sum(FactOperation.quantity), 0)
            ).label("avg_sale_price"),

            func.sum(FactOperation.quantity).label("quantity_sold"),
        )
        .outerjoin(DimProduct, FactOperation.dim_product_id == DimProduct.id)
        .join(DimDate, FactOperation.dim_date_id == DimDate.id)
        .filter(
            FactOperation.company_id == company_id,
            FactOperation.operation_type == OperationType.sale,
            FactOperation.unit_price.isnot(None),
            FactOperation.quantity.isnot(None),
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin,
        )
        .group_by(DimProduct.id, group_key, name_expr)
        .subquery()
    )
    # 🔹 Subquery de costos (PROMEDIO PONDERADO POR PERIODO)
    costo_sq = (
        db.query(
            group_key.label("group_key"),

            (
                func.sum(FactOperation.unit_price * FactOperation.quantity) /
                func.nullif(func.sum(FactOperation.quantity), 0)
            ).label("avg_cost"),
        )
        .outerjoin(DimProduct, FactOperation.dim_product_id == DimProduct.id)
        .join(DimDate, FactOperation.dim_date_id == DimDate.id)  # 🔥 IMPORTANTE
        .filter(
            FactOperation.company_id == company_id,
            FactOperation.operation_type == OperationType.purchase,
            FactOperation.unit_price.isnot(None),
            FactOperation.quantity.isnot(None),

            # 🔥 AQUÍ ESTÁ LA CLAVE
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin,
        )
        .group_by(group_key)
        .subquery()
    )

    # 🔹 Alias
    avg_sale = ventas_sq.c.avg_sale_price
    avg_cost = func.coalesce(costo_sq.c.avg_cost, 0)
    qty_sold = ventas_sq.c.quantity_sold

    # 🔥 Margen %
    margin_sql = (
        (avg_sale - avg_cost) / func.nullif(avg_sale, 0) * 100
    ).label("margin_pct")

    expenses_data = get_all_expenses(
        db,
        company_id,
        fecha_inicio,
        fecha_fin
    )

    # 🚀 Query final
    productos_rows = (
        db.query(
            ventas_sq.c.product_id,
            ventas_sq.c.name,
            avg_sale.label("avg_sale_price"),
            avg_cost.label("avg_cost"),
            qty_sold.label("quantity_sold"),

            # 💰 utilidad por unidad
            (avg_sale - avg_cost).label("utility_per_unit"),

            # 💰 totales correctos
            (avg_sale * qty_sold).label("total_ventas"),
            (avg_cost * qty_sold).label("total_costos"),
            ((avg_sale - avg_cost) * qty_sold).label("total_utilidad"),

            margin_sql,
        )
        .outerjoin(costo_sq, ventas_sq.c.group_key == costo_sq.c.group_key)
        .order_by(margin_sql.desc())
        .all()
    )

    # 🔹 Formateo
    def _f(val, decimals: int = 2) -> float:
        return round(float(val), decimals) if val is not None else 0.0

    productos_data = [
        {
            "id": row.product_id,
            "name": row.name,
            "avg_sale_price": _f(row.avg_sale_price),
            "avg_cost": _f(row.avg_cost),
            "quantity_sold": _f(row.quantity_sold, 0),
            "utility_per_unit": _f(row.utility_per_unit),
            "total_ventas": _f(row.total_ventas),
            "total_costos": _f(row.total_costos),
            "total_utilidad": _f(row.total_utilidad),
            "margin_pct": _f(row.margin_pct, 1),
        }
        for row in productos_rows
    ]
 
    # ── RETORNO ───────────────────────────────────────────────────────────────
    return {
        "period": {
            "fecha_inicio": str(fecha_inicio),
            "fecha_fin":    str(fecha_fin),
        },
        "available_metrics": available_metrics,
        "kpis": {
            "total_ventas":         total_ventas,
            "total_compras":        total_compras,
            "total_costos":         total_costos,
            "total_egresos":        total_egresos,
            "utilidad_bruta":       utilidad_bruta,
            "utilidad_operativa":   utilidad_operativa,
            "margen_ganancia_pct":  margen_ganancia,
            "ticket_promedio":      ticket_promedio,
            "total_transacciones":  total_transacciones,
        },
        "insights": {
            "top_producto":  top_producto[0]  if top_producto  else None,
            "top_proveedor": top_proveedor[0] if top_proveedor else None,
            "top_gasto":     top_gasto[0]     if top_gasto     else None,
        },
        "chart":      chart,
        "categories": categories_data,
        "expenses": expenses_data,
        # Tabla de productos con totales del período y margen (ordenada desc)
        "productos":  productos_data,
    }


def get_operation_breakdown(
    db: Session,
    company_id: int,
    operation_type: OperationType,
    fecha_inicio: date,
    fecha_fin: date,
):
    """Obtiene distribucion y metodos de pago para un tipo de operacion."""
    distribution = db.query(
        func.coalesce(DimProduct.name, DimCategory.name, FactOperation.concept).label("name"),
        func.sum(amount_expr).label("total"),
        func.sum(FactOperation.quantity).label("quantity")
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).outerjoin( 
        DimProduct, FactOperation.dim_product_id == DimProduct.id
    ).outerjoin( 
        DimCategory, FactOperation.dim_category_id == DimCategory.id
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == operation_type,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        func.coalesce(DimProduct.name, DimCategory.name, FactOperation.concept)
    ).all()

    payment_methods = db.query(
        DimPayment.type.label("payment_method"),
        func.sum(amount_expr).label("total")
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
    """Calcula utilidad por unidad con precio de venta y costo promedio."""
    group_key = func.coalesce(
        cast(FactOperation.dim_product_id, String),
        func.nullif(FactOperation.concept, "")
    )
    name_expr = func.coalesce(
        DimProduct.name,
        func.nullif(FactOperation.concept, ""),
        "Sin nombre"
    )

    # ── VENTAS ─────────────────────────────
    ventas = db.query(
        group_key.label("group_key"),
        name_expr.label("name"),
        (
            func.sum(FactOperation.unit_price * FactOperation.quantity) /
            func.nullif(func.sum(FactOperation.quantity), 0)
    ).label("avg_sale_price"),
        func.sum(FactOperation.quantity).label("total_quantity_sold")
    ).outerjoin(
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
        group_key,
        name_expr
    ).subquery()

    # ── COSTO PROMEDIO PONDERADO (mismo periodo) ──
    costo_historico = db.query(
        group_key.label("group_key"),
        (
            func.sum(FactOperation.unit_price * FactOperation.quantity) /
            func.nullif(func.sum(FactOperation.quantity), 0)
        ).label("avg_cost")                         
    ).outerjoin(
        DimProduct, FactOperation.dim_product_id == DimProduct.id
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id  
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.purchase,
        FactOperation.unit_price.isnot(None),
        FactOperation.quantity.isnot(None),           
        DimDate.full_date >= fecha_inicio,            
        DimDate.full_date <= fecha_fin,            
    ).group_by(
        group_key
    ).subquery()

    # ── RESULTADO FINAL ───────────────────
    results = db.query(
        ventas.c.name,
        ventas.c.avg_sale_price,
        costo_historico.c.avg_cost,
        ventas.c.total_quantity_sold,
        (
            ventas.c.avg_sale_price - func.coalesce(costo_historico.c.avg_cost, 0)
        ).label("utility_per_unit")
    ).outerjoin(
        costo_historico,
        ventas.c.group_key == costo_historico.c.group_key
    ).order_by(
        (
            ventas.c.avg_sale_price - func.coalesce(costo_historico.c.avg_cost, 0)
        ).desc()
    ).all()

    return [
        {
            "name": row.name,
            "avg_sale_price": float(row.avg_sale_price) if row.avg_sale_price else 0,
            "avg_cost": float(row.avg_cost) if row.avg_cost else 0,
            "quantity_sold": float(row.total_quantity_sold or 0),
            "utility_per_unit": float(row.utility_per_unit or 0),
        }
        for row in results
    ]

def get_categories_breakdown(
    db: Session,
    company_id: int,
    category_id: int,
    fecha_inicio: date,
    fecha_fin: date
):
    """Lista productos vendidos dentro de una categoria en un periodo."""
    products = db.query(
        DimProduct.id.label("id"),
        DimProduct.name.label("name"),
        func.sum(amount_expr).label("total"),
        func.sum(FactOperation.quantity).label("quantity")
    ).join(
        DimProduct, FactOperation.dim_product_id == DimProduct.id
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.sale,
        DimProduct.category_id == category_id,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).group_by(
        DimProduct.id,
        DimProduct.name
    )

    products_by_category = [
        {
            'id': row.id,
            'name': row.name,
            "value": float(row.total)
        }
        for row in products
    ]

    return products_by_category

def get_products_record(
      db: Session,
      company_id: int,
      product_id: int,
      fecha_inicio: date,
      fecha_fin: date
):
    """Devuelve payloads crudos de operaciones asociadas a un producto."""
    raw_record_product = db.query(
        RawRecord.id.label("id"),
        RawRecord.row_payload.label("payload")
    ).join(
        FactOperation, FactOperation.raw_record_id == RawRecord.id,
    ).join(
        DimProduct, FactOperation.dim_product_id == DimProduct.id
    ).join(
        DimDate, FactOperation.dim_date_id == DimDate.id
    ).filter(
        FactOperation.company_id == company_id,
        FactOperation.operation_type == OperationType.sale,
        DimProduct.id == product_id,
        DimDate.full_date >= fecha_inicio,
        DimDate.full_date <= fecha_fin
    ).all()
    
    payload = [
        {
            'id': row.id,
            'payload': row.payload
        }
        for row in raw_record_product
    ]

    return payload



def get_product_evolution(
    db,
    company_id: int,
    product_id: int,
    fecha_inicio: date,
    fecha_fin: date,
) -> dict:
    """Calcula evolucion de ventas, compras y utilidad de un producto."""

    delta = (fecha_fin - fecha_inicio).days

    # 🎯 Granularidad dinámica
    if delta <= 31:
        granularity = "daily"
        period = func.date_trunc('day', DimDate.full_date)
    elif delta <= 90:
        granularity = "weekly"
        period = func.date_trunc('week', DimDate.full_date)
    elif delta <= 365:
        granularity = "monthly"
        period = func.date_trunc('month', DimDate.full_date)
    else:
        granularity = "yearly"
        period = func.date_trunc('year', DimDate.full_date)

    # 🧠 Costo promedio global del periodo
    avg_cost_subquery = (
        db.query(
            (
                func.sum(FactOperation.unit_price * FactOperation.quantity) /
                func.nullif(func.sum(FactOperation.quantity), 0)
            )
        )
        .join(DimDate, FactOperation.dim_date_id == DimDate.id)
        .filter(
            FactOperation.company_id == company_id,
            FactOperation.dim_product_id == product_id,
            FactOperation.operation_type == OperationType.purchase,
            FactOperation.unit_price.isnot(None),
            FactOperation.quantity.isnot(None),
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin,
        )
        .scalar_subquery()
    )

    # 🚀 Query principal (UNA sola)
    rows = (
        db.query(
            period.label("period"),

            # 💰 Ventas
            func.sum(
                case(
                    (FactOperation.operation_type == OperationType.sale,
                     FactOperation.unit_price * FactOperation.quantity),
                    else_=0
                )
            ).label("ventas"),

            # 💸 Compras
            func.sum(
                case(
                    (FactOperation.operation_type == OperationType.purchase,
                     FactOperation.unit_price * FactOperation.quantity),
                    else_=0
                )
            ).label("compras"),

            # 🧠 Costo estimado usando promedio
            func.sum(
                case(
                    (FactOperation.operation_type == OperationType.sale,
                     FactOperation.quantity * avg_cost_subquery),
                    else_=0
                )
            ).label("costo_estimado"),
        )
        .join(DimDate, FactOperation.dim_date_id == DimDate.id)
        .filter(
            FactOperation.company_id == company_id,
            FactOperation.dim_product_id == product_id,
            FactOperation.unit_price.isnot(None),
            FactOperation.quantity.isnot(None),
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin,
        )
        .group_by(period)
        .order_by(period)
        .all()
    )

    data = []

    for row in rows:
        ventas = float(row.ventas or 0)
        compras = float(row.compras or 0)
        costo = float(row.costo_estimado or 0)

        utilidad = round(ventas - costo, 2)

        data.append({
            "period": row.period.strftime("%Y-%m-%d"),
            "ventas": round(ventas, 2),
            "compras": round(compras, 2),
            "utilidad": utilidad
        })

    return {
        "granularity": granularity,
        "data": data
    }

def get_all_expenses(
    db,
    company_id: int,
    fecha_inicio: date,
    fecha_fin: date
) -> dict:
    """Agrega todos los gastos por concepto dentro de un periodo."""
    rows = (
        db.query(
            FactOperation.concept.label("gasto"),
            func.sum(FactOperation.quantity).label("cantidad"),
            func.sum(FactOperation.total_amount).label("total")
        ).join(
            DimDate, FactOperation.dim_date_id == DimDate.id
        ).filter(
            FactOperation.company_id == company_id,
            FactOperation.operation_type == OperationType.expense,
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin
        ).group_by(
            FactOperation.concept,
        ).all()
    )

    expenses = [
        {
            'gasto': row.gasto,
            'value': float(row.total)
        }
        for row in rows
    ]

    return expenses

def get_expense_evolution(
    db,
    company_id: int,
    expense_name: str,
    fecha_inicio: date,
    fecha_fin: date,
) -> dict:
    """Calcula la evolucion temporal de un concepto de gasto."""

    delta = (fecha_fin - fecha_inicio).days

    if delta <= 31:
        granularity = "daily"
        period = func.date_trunc('day', DimDate.full_date)
        date_format = "%Y-%m-%d"
    elif delta <= 90:
        granularity = "weekly"
        period = func.date_trunc('week', DimDate.full_date)
        date_format = "%Y-%m-%d"  # inicio de la semana
    elif delta <= 365:
        granularity = "monthly"
        period = func.date_trunc('month', DimDate.full_date)
        date_format = "%Y-%m"
    else:
        granularity = "yearly"
        period = func.date_trunc('year', DimDate.full_date)
        date_format = "%Y"

    rows = (
        db.query(
            period.label("period"),
            func.sum(FactOperation.total_amount).label("gasto_total"),
            func.count(FactOperation.id).label("num_operaciones"),
        )
        .join(DimDate, FactOperation.dim_date_id == DimDate.id)
        .filter(
            FactOperation.company_id == company_id,
            FactOperation.operation_type == OperationType.expense,
            FactOperation.concept == expense_name,
            DimDate.full_date >= fecha_inicio,
            DimDate.full_date <= fecha_fin,
        )
        .group_by(period)
        .order_by(period)
        .all()
    )

    data = []

    for row in rows:
        gasto = float(row.gasto_total or 0)

        data.append({
            "period": row.period.strftime(date_format),
            "gasto_total": round(gasto, 2),
            "num_operaciones": row.num_operaciones,
        })

    return {
        "granularity": granularity,
        "data": data
    }
