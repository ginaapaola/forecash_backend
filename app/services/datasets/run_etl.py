from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.dataset.dataset_enum import DatasetStatus, OperationTypeDataset
from app.models.dataset.raw_dataset import RawDataset
from app.models.dataset.raw_record import RawRecord
from app.models.dimensions.operation_type import OperationType
from app.models.fact.fact_operation import FactOperation

from app.services.datasets.dimensions.get_or_create_dim import (
    _get_or_create_dim_category,
    _get_or_create_dim_client,
    _get_or_create_dim_date,
    _get_or_create_dim_payment,
    _get_or_create_dim_product,
    _get_or_create_dim_supplier,
)

OPERATION_TYPE_MAP = {
    "venta": OperationType.sale,
    "compra": OperationType.purchase,
    "costo": OperationType.expense,
}


def clean(value):
    return str(value).strip() if value else None


def run_etl(db: Session, raw_dataset: RawDataset) -> dict:
    records = db.query(RawRecord).filter(
        RawRecord.raw_dataset_id == raw_dataset.id
    ).all()

    mapping = raw_dataset.column_mapping.get("mapped", {})
    company_id = raw_dataset.company_id

    processed = 0
    skipped = 0
    errors = []

    # 🔥 CACHE
    product_cache = {}
    category_cache = {}
    client_cache = {}
    supplier_cache = {}
    payment_cache = {}
    date_cache = {}

    # 🔥 BULK INSERT
    facts_to_insert = []

    # ─────────────────────────────────────────────
    # Helpers con cache
    # ─────────────────────────────────────────────

    def get_category_cached(name):
        key = name.strip().lower()
        if key in category_cache:
            return category_cache[key]

        dim = _get_or_create_dim_category(db, name)
        category_cache[key] = dim
        return dim

    def get_product_cached(name, dim_category):
        key = (name.strip().lower(), company_id)
        if key in product_cache:
            return product_cache[key]

        dim = _get_or_create_dim_product(
            db,
            name,
            company_id,
            dim_category
        )
        product_cache[key] = dim
        return dim

    def get_date_cached(fecha):
        if fecha in date_cache:
            return date_cache[fecha]

        dim = _get_or_create_dim_date(db, fecha)
        date_cache[fecha] = dim
        return dim

    def get_client_cached(name):
        key = (name.strip().lower(), company_id)
        if key in client_cache:
            return client_cache[key]

        dim = _get_or_create_dim_client(db, name, company_id)
        client_cache[key] = dim
        return dim

    def get_supplier_cached(name):
        key = (name.strip().lower(), company_id)
        if key in supplier_cache:
            return supplier_cache[key]

        dim = _get_or_create_dim_supplier(db, name, company_id)
        supplier_cache[key] = dim
        return dim

    def get_payment_cached(name):
        key = name.strip().lower()
        if key in payment_cache:
            return payment_cache[key]

        dim = _get_or_create_dim_payment(db, name)
        payment_cache[key] = dim
        return dim

    # ─────────────────────────────────────────────
    # Loop principal
    # ─────────────────────────────────────────────

    for record in records:
        payload = record.row_payload

        try:
            dataset_operation_type = raw_dataset.operation_type

            raw_fecha = payload.get(mapping.get("fecha"))
            raw_total = payload.get(mapping.get("valor_total")) or payload.get(mapping.get("total_amount"))
            raw_tipo = payload.get(mapping.get("tipo_operacion"))

            if not raw_tipo:
                raw_tipo = {
                    OperationTypeDataset.sale: "venta",
                    OperationTypeDataset.purchase: "compra",
                    OperationTypeDataset.expense: "costo",
                }.get(dataset_operation_type)

            if raw_fecha is None or raw_tipo is None or raw_total is None:
                skipped += 1
                errors.append(f"Fila {record.row_number}: faltan campos obligatorios.")
                continue

            fecha = date.fromisoformat(raw_fecha) if isinstance(raw_fecha, str) else raw_fecha
            operation_type = OPERATION_TYPE_MAP.get(str(raw_tipo).strip().lower())

            if not operation_type:
                skipped += 1
                errors.append(f"Fila {record.row_number}: tipo_operacion '{raw_tipo}' no reconocido.")
                continue

            total_amount = Decimal(str(raw_total))

            # ── DIM DATE ─────────────────────────
            dim_date = get_date_cached(fecha)

            # ── CATEGORY ─────────────────────────
            dim_category = None
            raw_category = clean(payload.get(mapping.get("dim_category")))

            if raw_category:
                dim_category = get_category_cached(raw_category)

            # ── PRODUCT ─────────────────────────
            dim_product = None
            raw_product = clean(payload.get(mapping.get("dim_product")))

            if raw_product:
                dim_product = get_product_cached(raw_product, dim_category)

            # ── OTRAS DIMS ──────────────────────
            dim_client = None
            raw_client = clean(payload.get(mapping.get("dim_client")))
            if raw_client:
                dim_client = get_client_cached(raw_client)

            dim_supplier = None
            raw_supplier = clean(payload.get(mapping.get("dim_supplier")))
            if raw_supplier:
                dim_supplier = get_supplier_cached(raw_supplier)

            dim_payment = None
            raw_payment = clean(payload.get(mapping.get("dim_payment")))
            if raw_payment:
                dim_payment = get_payment_cached(raw_payment)

            # ── CAMPOS FACT ─────────────────────
            concept = (
                payload.get(mapping.get("concept"))
                or raw_product
                or raw_category
                or "Sin nombre"
            )

            raw_quantity = payload.get(mapping.get("quantity"))
            raw_unit_price = payload.get(mapping.get("unit_price"))
            raw_subtotal = payload.get(mapping.get("subtotal"))

            quantity = Decimal(str(raw_quantity)) if raw_quantity else Decimal("1")
            unit_price = Decimal(str(raw_unit_price)) if raw_unit_price else None

            # 🔥 LÓGICA CORRECTA DE SUBTOTAL
            if raw_subtotal:
                subtotal = Decimal(str(raw_subtotal))
            elif unit_price and quantity:
                subtotal = unit_price * quantity
            else:
                subtotal = total_amount

            fact = FactOperation(
                raw_record_id=record.id,
                raw_dataset_id=raw_dataset.id,
                company_id=company_id,
                operation_type=operation_type,
                concept=concept,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal,
                total_amount=total_amount,
                dim_date_id=dim_date.id,
                dim_product_id=dim_product.id if dim_product else None,
                dim_category_id=dim_category.id if dim_category else None,
                dim_client_id=dim_client.id if dim_client else None,
                dim_supplier_id=dim_supplier.id if dim_supplier else None,
                dim_payment_id=dim_payment.id if dim_payment else None,
            )

            facts_to_insert.append(fact)
            processed += 1

        except Exception as e:
            skipped += 1
            errors.append(f"Fila {record.row_number}: {str(e)}")

    # 🔥 BULK INSERT
    if facts_to_insert:
        db.bulk_save_objects(facts_to_insert)

    # ── STATUS ────────────────────────────────
    raw_dataset.status = (
        DatasetStatus.processed
        if skipped == 0
        else DatasetStatus.processed_with_errors
    )

    raw_dataset.etl_summary = {
        "processed": processed,
        "skipped": skipped,
        "errors": errors[:50],
    }

    db.commit()

    return raw_dataset.etl_summary