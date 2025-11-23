import csv
from typing import List
from models.csv_model import CSVData

class CSVServiceError(Exception):
    pass

class CSVService:
    """
    Lee CSV con autodetección de delimitador y normaliza filas.
    No convierte decimales (deja todo como strings) — UI/negocio hará parse si lo necesita.
    """

    @staticmethod
    def read_csv(path: str) -> CSVData:
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                sample = f.read(4096)
                f.seek(0)
                # detectar dialecto (delimitador) entre los comunes
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
                except Exception:
                    # fallback: preferir coma, si hay tab en muestra usar tab
                    if "\t" in sample:
                        dialect = csv.excel_tab
                    else:
                        dialect = csv.excel

                reader = csv.reader(f, dialect)
                data = list(reader)
        except Exception as e:
            raise CSVServiceError(f"No se pudo leer el archivo: {e}")

        if not data:
            raise CSVServiceError("El archivo CSV está vacío.")

        columns = [col.strip() for col in data[0]]
        rows_raw = data[1:]

        # Normalizar filas: rellenar con "" o cortar si sobran columnas
        normalized_rows: List[List[str]] = []
        col_count = len(columns)
        for i, row in enumerate(rows_raw):
            row = [cell.strip() for cell in row]
            if len(row) < col_count:
                row = row + [""] * (col_count - len(row))
            elif len(row) > col_count:
                row = row[:col_count]
            normalized_rows.append(row)

        return CSVData(columns=columns, rows=normalized_rows)