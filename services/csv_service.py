import csv
from typing import List
from models.csv_model import CSVData
import io

class CSVServiceError(Exception):
    pass

class CSVService:
    """
    Servicio robusto para leer CSVs 'sucios'.
    - Soporta múltiples codificaciones (UTF-8, Latin-1).
    - Repara filas rotas por comas decimales (ej: 0,78 -> 0.78).
    """

    @staticmethod
    def read_csv(path: str) -> CSVData:
        # 1. Intentar leer con diferentes codificaciones
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
        lines = None
        
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc, newline="") as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                break # Si lee bien, salimos del bucle
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise CSVServiceError(f"Error de lectura: {e}")

        if not lines:
            raise CSVServiceError("No se pudo leer el archivo o está vacío (revise codificación).")

        # 2. Detectar delimitador basado en la primera línea (Header)
        header_line = lines[0]
        possible_delimiters = [',', ';', '\t', '|']
        
        # Contar ocurrencias y elegir el ganador
        delimiter = max(possible_delimiters, key=lambda d: header_line.count(d))
        
        # Si no encontró ninguno, por defecto coma
        if header_line.count(delimiter) == 0:
            delimiter = ','

        # 3. Parsear encabezado
        reader = csv.reader(io.StringIO(header_line), delimiter=delimiter)
        columns = next(reader)
        columns = [c.strip() for c in columns]
        expected_cols = len(columns)

        # 4. Procesar filas con "Reparación de Decimales"
        normalized_rows = []
        
        for line in lines[1:]:
            # Parsear línea actual
            row_reader = csv.reader(io.StringIO(line), delimiter=delimiter)
            try:
                row = next(row_reader)
            except StopIteration:
                continue

            row = [cell.strip() for cell in row]
            current_cols = len(row)

            # CASO A: Fila Perfecta
            if current_cols == expected_cols:
                normalized_rows.append(row)
            
            # CASO B: Fila Rota (Tiene más columnas de las esperadas)
            elif current_cols > expected_cols:
                # Unimos las columnas sobrantes al final (asumiendo que es el valor decimal partido)
                # Ejemplo: [Fecha, 0, 79] -> [Fecha, 0,79]
                new_row = []
                safe_part_idx = expected_cols - 1 
                new_row.extend(row[:safe_part_idx])
                
                rest_of_row = row[safe_part_idx:]
                # Unimos con coma para conservar formato visual original
                reconstructed_value = ",".join(rest_of_row) 
                
                new_row.append(reconstructed_value)
                normalized_rows.append(new_row)

            # CASO C: Faltan columnas (Rellenar)
            elif current_cols < expected_cols:
                row = row + [""] * (expected_cols - current_cols)
                normalized_rows.append(row)

        return CSVData(columns=columns, rows=normalized_rows)