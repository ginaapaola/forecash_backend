from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.dataset.dataset_enum import DatasetStatus, OperationTypeDataset
from app.models.dataset.raw_dataset import RawDataset
from app.models.dataset.raw_record import RawRecord
from app.models.dimensions.operation_type import OperationType
from app.models.fact.fact_operation import FactOperation
from app.services.datasets.dimensions.get_or_create_dim import _get_or_create_dim_category, _get_or_create_dim_client, _get_or_create_dim_date, _get_or_create_dim_payment, _get_or_create_dim_product, _get_or_create_dim_supplier

OPERATION_TYPE_MAP = {
    "venta": OperationType.sale,
    "compra": OperationType.purchase,
    "costo": OperationType.expense,
}

@staticmethod
def run_etl(db: Session, raw_dataset: RawDataset) -> dict:
    """
    Procesa los RawRecords de un dataset y puebla las tablas
    Dim y FactOperation. Actualiza el status del RawDataset.
    
    Retorna un resumen del proceso.
    """
    records = db.query(RawRecord).filter(
        RawRecord.raw_dataset_id == raw_dataset.id
    ).all()

    mapping = raw_dataset.column_mapping.get("mapped", {})
    company_id = raw_dataset.company_id

    processed = 0
    skipped = 0
    errors = []

    for record in records:
        payload = record.row_payload
        try:
            # ── Campos obligatorios ─────────────────────────────
            dataset_operation_type = raw_dataset.operation_type
            
            raw_fecha = payload.get(mapping.get("fecha"))
            raw_total = payload.get(mapping.get("valor_total"))

            raw_tipo = payload.get(mapping.get("tipo_operacion"))

            if not raw_tipo:
                # usar tipo del dataset
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

            # ── Dims obligatorias ───────────────────────────────
            dim_date = _get_or_create_dim_date(db, fecha)

            # ── Dims opcionales ─────────────────────────────────
            dim_product = None
            raw_product = payload.get(mapping.get("dim_product"))
            if raw_product:
                dim_product = _get_or_create_dim_product(db, raw_product, company_id)

            dim_category = None
            raw_category = payload.get(mapping.get("dim_category"))
            if raw_category:
                dim_category = _get_or_create_dim_category(db, raw_category)

            dim_client = None
            raw_client = payload.get(mapping.get("dim_client"))
            if raw_client:
                dim_client = _get_or_create_dim_client(db, raw_client, company_id)

            dim_supplier = None
            raw_supplier = payload.get(mapping.get("dim_supplier"))
            if raw_supplier:
                dim_supplier = _get_or_create_dim_supplier(db, raw_supplier, company_id)

            dim_payment = None
            raw_payment = payload.get(mapping.get("dim_payment"))
            if raw_payment:
                dim_payment = _get_or_create_dim_payment(db, raw_payment)

            # ── Campos opcionales de FactOperation ──────────────
            concept = payload.get(mapping.get("concept"))
            raw_quantity = payload.get(mapping.get("quantity"))
            raw_unit_price = payload.get(mapping.get("unit_price"))

            quantity = Decimal(str(raw_quantity)) if raw_quantity else Decimal("1")
            unit_price = Decimal(str(raw_unit_price)) if raw_unit_price else None
            subtotal = unit_price * quantity if unit_price else total_amount

            # ── Crear FactOperation ─────────────────────────────
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
            db.add(fact)
            processed += 1

        except Exception as e:
            skipped += 1
            errors.append(f"Fila {record.row_number}: {str(e)}")

    # ── Actualizar status del dataset ───────────────────────────
    raw_dataset.status = DatasetStatus.processed if skipped == 0 else DatasetStatus.processed_with_errors
    raw_dataset.etl_summary = {
        "processed": processed,
        "skipped": skipped,
        "errors": errors[:50],  # limitar para no saturar el campo
    }
    db.commit()

    return raw_dataset.etl_summary