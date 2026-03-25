import pandas as pd
import io
import numpy as np

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.models.dataset.dataset_enum import DatasetStatus, FileType, OperationTypeDataset
from app.models.dataset.raw_dataset import RawDataset
from app.models.dataset.raw_record import RawRecord
from app.services.datasets.mapping.mapping_service import MappingService

class DatasetService:

    @staticmethod
    def _sanitize_for_json(obj):
        if isinstance(obj, dict):
            return {k: DatasetService._sanitize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DatasetService._sanitize_for_json(i) for i in obj]
        elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
            return None
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return None if np.isnan(obj) or np.isinf(obj) else float(obj)
        elif isinstance(obj, pd.Timestamp):
            return obj.strftime("%Y-%m-%d")
        elif hasattr(obj, 'isoformat'):  # cubre datetime y date nativos también
            return obj.isoformat()
        return obj

    @staticmethod
    async def process_file(
            file: UploadFile,
            db: Session,
            company_id: int,
            uploaded_by: int
        ):

        contents = await file.read()

        # 1. Validar extensión
        if not file.filename.endswith((".csv", ".xlsx")):
            raise HTTPException(status_code=400, detail="Formato no permitido")

        try:
            # 2. Leer archivo
            if file.filename.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(contents))
            else:
                df = pd.read_excel(io.BytesIO(contents))

            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.where(pd.notnull(df), None)

            # 🔥 AUTOCÁLCULO DE valor_total
            if "valor_total" in df.columns:
                if df["valor_total"].isnull().all():

                    if "cantidad" in df.columns and "precio_unitario" in df.columns:
                        df["valor_total"] = df["cantidad"] * df["precio_unitario"]

            # 3. Obtener info
            headers = list(df.columns)
            preview = df.head().to_dict(orient="records")
            

            validation = DatasetService.validate_dataframe(df)
           # metrics = DatasetService.calculate_metrics(df)

            raw_dataset_id = None
            if validation["is_valid"]:
                file_type = FileType.csv if file.filename.endswith(".csv") else FileType.xlsx
                raw_dataset = await DatasetService.save_raw_dataset(
                    db=db,
                    df=df,
                    file_name=file.filename,
                    file_type=file_type,
                    company_id=company_id,
                    uploaded_by=uploaded_by,
                )
                raw_dataset_id = raw_dataset.id

            return DatasetService._sanitize_for_json({
                "file_name": file.filename,
                "columns": headers,
                "rows": len(df),
                "preview": preview,
                "validation": validation,
               # "metrics": metrics
                "raw_dataset_id": raw_dataset_id, #SI NO PASÓ LA VALIDACIÓN ES NONE
            })

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> dict:
        REQUIRED_COLUMNS = {"fecha", "tipo_operacion", "valor_total"}
        VALID_OPERATIONS = {"venta", "compra", "costo"}

        errors = []
        warnings = []
        detected_types = {}

        # ── 1. Archivo vacío ──────────────────────────────────
        if df.empty:
            return {
                "is_valid": False,
                "errors": ["El archivo está vacío."],
                "warnings": [],
                "summary": {}
            }

        # ── 2. Normalizar columnas ────────────────────────────
        df.columns = [col.strip().lower() for col in df.columns]
        total_rows = len(df)

        # ── 3. Validar columnas obligatorias ─────────────────
        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            return {
                "is_valid": False,
                "errors": [f"Faltan columnas obligatorias: {', '.join(sorted(missing))}"],
                "warnings": [],
                "summary": {}
            }

        # ── 4. Tipos de datos ────────────────────────────────
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                detected_types[col] = "numeric"
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                detected_types[col] = "date"
            else:
                detected_types[col] = "text"

        # Intentar detectar fechas en columnas tipo texto
        for col in df.columns:
            if detected_types[col] == "text":
                parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
                if parsed.notna().sum() > total_rows * 0.8:
                    detected_types[col] = "date"
                    df[col] = parsed

        # ── 5. valor_total ───────────────────────────────────
        df["valor_total"] = pd.to_numeric(df["valor_total"], errors="coerce")
        df["valor_total"] = df["valor_total"].replace([float("inf"), float("-inf")], None)

        null_values = df["valor_total"].isna().sum()

        if null_values == total_rows:
            errors.append("La columna 'valor_total' no tiene valores numéricos válidos.")
        elif null_values > 0:
            warnings.append(f"'valor_total' tiene {null_values} valores nulos o inválidos.")

        # ── 6. tipo_operacion ────────────────────────────────
        df["tipo_operacion"] = df["tipo_operacion"].astype(str).str.strip().str.lower()

        invalid_ops = ~df["tipo_operacion"].isin(VALID_OPERATIONS)
        invalid_count = invalid_ops.sum()

        if invalid_count == total_rows:
            errors.append("No hay valores válidos en 'tipo_operacion'.")
        elif invalid_count > 0:
            warnings.append(f"{invalid_count} valores no reconocidos en 'tipo_operacion'.")

        # ── 7. Nulos en columnas clave ───────────────────────
        for col in REQUIRED_COLUMNS:
            nulls = df[col].isnull().sum()
            if nulls > 0:
                pct = round((nulls / total_rows) * 100, 1)
                warnings.append(f"'{col}' tiene {nulls} nulos ({pct}%).")

        # ── 8. Summary ──────────────────────────────────────
        summary = {
            "total_rows": total_rows,
            "total_columns": len(df.columns),
            "operations_found": {
                str(k): int(v)
                for k, v in df["tipo_operacion"]
                .value_counts()
                .to_dict()
                .items()
                if k in VALID_OPERATIONS
            }
        }

        # 🔥 date_range (se mantiene como pediste)
        if df["fecha"].notna().any():
            fecha_series = pd.to_datetime(df["fecha"], errors="coerce", dayfirst=True).dropna()

            if not fecha_series.empty:
                summary["date_range"] = {
                    "from": fecha_series.min().strftime("%Y-%m-%d"),
                    "to": fecha_series.max().strftime("%Y-%m-%d"),
                }

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "detected_types": detected_types,
            "summary": summary,
        }

        
    """@staticmethod
    def calculate_metrics(df: pd.DataFrame):

        metrics = {}

        # Normalizar texto (evita errores por mayúsculas)
        df["tipo_operacion"] = df["tipo_operacion"].str.lower()

        # Filtrar por tipo
        ventas = df[df["tipo_operacion"] == "venta"]
        costos = df[df["tipo_operacion"] == "costo"]
        compras = df[df["tipo_operacion"] == "compra"]

        # Cálculos principales
        metrics["total_ventas"] = int(ventas["valor_total"].sum())
        metrics["total_costos"] = int(costos["valor_total"].sum())
        metrics["total_compras"] = int(compras["valor_total"].sum())

        # Utilidad
        metrics["utilidad_bruta"] = (
            metrics["total_ventas"] -
            (metrics["total_costos"]
            + metrics["total_compras"])
        )

        return metrics"""
    
    @staticmethod
    def _detect_operation_type(df: pd.DataFrame) -> OperationTypeDataset:
        ops = set(df["tipo_operacion"].astype(str).str.strip().str.lower().unique())
        ops = ops & {"venta", "compra", "costo"}

        if ops == {"venta"}:
            return OperationTypeDataset.sale
        elif ops == {"compra"}:
            return OperationTypeDataset.purchase
        elif ops == {"costo"}:
            return OperationTypeDataset.expense
        else: return OperationTypeDataset.mixed

    @staticmethod
    async def save_raw_dataset(
        db: Session, 
        df: pd.DataFrame, 
        file_name: str, 
        file_type: FileType, 
        company_id: int, 
        uploaded_by: int
    ) -> RawDataset:
        
        operation_type = DatasetService._detect_operation_type(df)

        raw_dataset = RawDataset(
            company_id=company_id,
            uploaded_by=uploaded_by,
            file_name=file_name,
            file_type=file_type,
            operation_type=operation_type,
            status=DatasetStatus.pending,
        )

        column_mapping = MappingService.infer_column_mapping(df)
        raw_dataset.column_mapping = column_mapping

        db.add(raw_dataset)
        db.flush()

        records = []
        for i, row in enumerate(df.to_dict(orient="records"), start=1):
            clean_row = DatasetService._sanitize_for_json(row)
            records.append(RawRecord(
                raw_dataset_id=raw_dataset.id,
                row_number=i,
                row_payload=clean_row,
            ))

        db.add_all(records)
        db.commit()
        db.refresh(raw_dataset)

        return raw_dataset