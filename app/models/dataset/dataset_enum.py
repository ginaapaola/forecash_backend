import enum


class FileType(str, enum.Enum):
    csv = "csv"
    xlsx = "xlsx"


class DatasetStatus(str, enum.Enum):
    """
    Ciclo de vida del dataset dentro del pipeline ETL

    pending   → archivo recibido, aún no guardado en staging
    staged    → Raw_records insertados, esperando ETL
    processed → Fact_operations generadas correctamente
    error     → falló en validación o en el ETL
    """

    pending = "pending"
    processed = "processed"
    processed_with_errors = "processed_with_errors"
    error = "error"


class OperationTypeDataset(str, enum.Enum):
    """Tipo de operación que representa el dataset"""

    sale = 'sale'           #ventas
    purchase = 'purchase'   #compras
    expense = "expense"     #gastos / costos
    mixed = "mixed"         #ell dataset contiene más de un tipo