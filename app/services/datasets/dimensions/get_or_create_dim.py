from datetime import date

from sqlalchemy.orm import Session

from app.models.dimensions.dim_category import DimCategory
from app.models.dimensions.dim_client import DimClient
from app.models.dimensions.dim_date import DimDate
from app.models.dimensions.dim_payment import DimPayment
from app.models.dimensions.dim_product import DimProduct
from app.models.dimensions.dim_supplier import DimSupplier


@staticmethod
def _get_or_create_dim_date(db: Session, fecha: date) -> DimDate:
    dim = db.query(DimDate).filter(DimDate.full_date == fecha).first()
    if not dim:
        dim = DimDate(
            full_date=fecha,
            day=fecha.day,
            week=fecha.isocalendar()[1],
            month=fecha.month,
            year=fecha.year
        )
        db.add(dim)
        db.flush()
    return dim

@staticmethod
def _get_or_create_dim_category(db: Session, name: str) -> DimCategory:
    name_clean = name.strip().lower()
    dim = db.query(DimCategory).filter(DimCategory.name == name_clean).first()
    if not dim:
        dim = DimCategory(name=name_clean)
        db.add(dim)
        db.flush()
    return dim

@staticmethod
def _get_or_create_dim_client(db: Session, name: str, company_id: int) -> DimClient: 
    name_clean = name.strip().lower()
    dim = db.query(DimClient).filter(
            DimClient.name == name_clean,
            DimClient.company_id == company_id
        ).first()
    if not dim:
        dim = DimClient(name=name_clean, company_id=company_id)
        db.add(dim)
        db.flush()
    return dim

@staticmethod
def _get_or_create_dim_payment(db: Session, payment_type: str) -> DimPayment:
    type_clean = payment_type.strip().lower()
    dim = db.query(DimPayment).filter(DimPayment.type == type_clean).first()
    if not dim: 
        dim = DimPayment(type=type_clean)
        db.add(dim)
        db.flush()
    return dim

@staticmethod
def _get_or_create_dim_product(
    db: Session,
    product: str,
    company_id: int,
    dim_category=None  # 👈 ahora recibe el objeto
) -> DimProduct:

    product_clean = product.strip().lower()

    dim = db.query(DimProduct).filter(
        DimProduct.name == product_clean,
        DimProduct.company_id == company_id
    ).first()

    if not dim:
        dim = DimProduct(
            name=product_clean,
            company_id=company_id,
            category_id=dim_category.id if dim_category else None  # 👈 FIX
        )
        db.add(dim)
        db.flush()

    else:
        # 🔥 opcional: asignar categoría si no tiene
        if not dim.category_id and dim_category:
            dim.category_id = dim_category.id

    return dim

@staticmethod
def _get_or_create_dim_supplier(db: Session, supplier: str, company_id: int) -> DimSupplier:
    supplier_clean = supplier.strip().lower()
    dim = db.query(DimSupplier).filter(
        DimSupplier.name == supplier_clean,
        DimSupplier.company_id == company_id
    ).first()
    if not dim:
        dim = DimSupplier(name=supplier_clean, company_id=company_id)
        db.add(dim)
        db.flush()
    return dim