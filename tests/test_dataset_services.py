from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

import app.services.datasets.dataset_services as dataset_module
from app.models.dataset.dataset_enum import OperationTypeDataset
from app.services.datasets.dataset_services import DatasetService


class DummyUploadFile:
    def __init__(self, filename, content):
        self.filename = filename
        self._content = content

    async def read(self):
        return self._content


def test_validate_dataframe_accepts_valid_file_with_synonyms():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02"],
            "total": [1200, 800],
            "tipo": ["venta", "compra"],
        }
    )

    result = DatasetService.validate_dataframe(df)

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert result["summary"]["total_rows"] == 2
    assert result["summary"]["operations_found"] == {"venta": 1, "compra": 1}
    assert result["summary"]["date_range"] == {
        "from": "2026-01-01",
        "to": "2026-01-02",
    }


def test_validate_dataframe_rejects_empty_file():
    result = DatasetService.validate_dataframe(pd.DataFrame())

    assert result["is_valid"] is False
    assert result["errors"][0].startswith("El archivo")
    assert result["warnings"] == []
    assert result["summary"] == {}


def test_validate_dataframe_reports_missing_required_columns_without_crashing():
    df = pd.DataFrame({"fecha": ["2026-01-01"], "producto": ["Cafe"]})

    result = DatasetService.validate_dataframe(df)

    assert result["is_valid"] is False
    assert result["errors"] == ["Faltan columnas obligatorias: valor_total"]


def test_validate_dataframe_rejects_total_column_without_numeric_values():
    df = pd.DataFrame(
        {
            "fecha": ["2026-01-01", "2026-01-02"],
            "valor_total": ["abc", None],
            "tipo_operacion": ["venta", "venta"],
        }
    )

    result = DatasetService.validate_dataframe(df)

    assert result["is_valid"] is False
    assert any("valor_total" in error and "num" in error for error in result["errors"])


def test_detect_operation_type_from_operation_column():
    df = pd.DataFrame({"tipo_operacion": ["venta", "venta"]})

    assert DatasetService._detect_operation_type(df) == OperationTypeDataset.sale


def test_detect_operation_type_from_columns_when_operation_column_is_missing():
    df = pd.DataFrame({"proveedor": ["ACME"], "total_compra": [100]})

    assert DatasetService._detect_operation_type(df) == OperationTypeDataset.purchase


def test_sanitize_for_json_converts_non_json_values():
    payload = {
        "nan": np.nan,
        "inf": np.inf,
        "int": np.int64(10),
        "float": np.float64(1.5),
        "date": pd.Timestamp("2026-01-01"),
        "items": [np.float64(np.nan), np.int64(3)],
    }

    result = DatasetService._sanitize_for_json(payload)

    assert result == {
        "nan": None,
        "inf": None,
        "int": 10,
        "float": 1.5,
        "date": "2026-01-01",
        "items": [None, 3],
    }


@pytest.mark.asyncio
async def test_process_file_rejects_unsupported_extension():
    file = DummyUploadFile("datos.txt", b"fecha,valor_total\n2026-01-01,100\n")

    with pytest.raises(HTTPException) as exc:
        await DatasetService.process_file(file, db=None, company_id=1, uploaded_by=2)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Formato no permitido"


@pytest.mark.asyncio
async def test_process_file_saves_valid_csv_and_runs_etl(monkeypatch):
    csv_content = (
        "fecha,valor_total,cantidad,precio_unitario,tipo_operacion\n"
        "2026-01-01,,2,1500,venta\n"
    ).encode()
    file = DummyUploadFile("ventas.csv", csv_content)
    saved_dataset = SimpleNamespace(id=99)
    calls = {}

    async def fake_save_raw_dataset(**kwargs):
        calls["save"] = kwargs
        return saved_dataset

    def fake_run_etl(db, raw_dataset):
        calls["etl"] = (db, raw_dataset)
        return {"processed": 1, "skipped": 0, "errors": []}

    monkeypatch.setattr(DatasetService, "save_raw_dataset", fake_save_raw_dataset)
    monkeypatch.setattr(dataset_module, "run_etl", fake_run_etl)

    result = await DatasetService.process_file(
        file,
        db="db-session",
        company_id=10,
        uploaded_by=20,
    )

    assert result["file_name"] == "ventas.csv"
    assert result["rows"] == 1
    assert result["validation"]["is_valid"] is True
    assert result["raw_dataset_id"] == 99
    assert result["etl_summary"] == {"processed": 1, "skipped": 0, "errors": []}
    assert calls["save"]["company_id"] == 10
    assert calls["save"]["uploaded_by"] == 20
    assert calls["save"]["df"].loc[0, "valor_total"] == 3000
    assert calls["etl"] == ("db-session", saved_dataset)
