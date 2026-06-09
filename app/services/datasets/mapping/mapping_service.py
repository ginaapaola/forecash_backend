import pandas as pd

from app.services.datasets.mapping.column_mapping import COLUMN_MAPPING_RULES


class MappingService:
    @staticmethod
    def infer_column_mapping(df: pd.DataFrame) -> dict:
        """
        Infiere el mapeo entre columnas del archivo y campos de Forecash.
        Retorna un dict con:
        - mapped: columnas que se pudieron mapear
        - unmapped: columnas del archivo que no se reconocieron
        """
        df_cols = {col.strip().lower(): col for col in df.columns}
        mapped = {}
        matched_df_cols = set()

        for forecash_field, synonyms in COLUMN_MAPPING_RULES.items():
            for synonym in synonyms:
                if synonym in df_cols:
                    original_col = df_cols[synonym]
                    mapped[forecash_field] = original_col
                    matched_df_cols.add(synonym)
                    break  # primera coincidencia gana, no seguir buscando

        unmapped = [
            col for col in df.columns
            if col.strip().lower() not in matched_df_cols
        ]

        return {
            "mapped": mapped,
            "unmapped": unmapped
        }