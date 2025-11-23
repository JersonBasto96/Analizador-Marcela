from services.csv_service import CSVService, CSVServiceError
from models.csv_model import CSVData
from typing import Dict, List, Tuple

class CSVController:
    """
    Controlador que orquesta lectura y parseo semántico del CSV.
    Detecta pares: "Fecha Hora <Device>"  +  "<Device>"
    """

    def __init__(self):
        self.csv_data: CSVData | None = None
        # device_name -> (fecha_col_name, value_col_name)
        self.device_columns = {}
        self._analysis_cache = {}

    def load_csv(self, path: str):
        try:
            self.csv_data = CSVService.read_csv(path)
            self._analysis_cache.clear()
        except CSVServiceError:
            raise
        except Exception as e:
            raise CSVServiceError(f"Error inesperado al leer CSV: {e}")

        if not self.csv_data.columns:
            raise CSVServiceError("CSV sin encabezados.")

        if len(self.csv_data.columns) < 2:
            raise CSVServiceError("El CSV no tiene suficientes columnas.")

        self._parse_device_pairs()

        if not self.device_columns:
            raise CSVServiceError("No se encontraron pares válidos 'Fecha Hora' + 'Device' en encabezados.")

        return self.csv_data

    def _parse_device_pairs(self):
        """Versión mejorada con mejor detección"""
        self.device_columns = {}
        cols = [col.strip() for col in self.csv_data.columns]
        
        i = 0
        while i + 1 < len(cols):
            fecha_col = cols[i]
            value_col = cols[i + 1]
            
            # Detección más flexible de columnas de fecha
            fecha_lower = fecha_col.lower()
            is_date_column = (
                "fecha" in fecha_lower or 
                "hora" in fecha_lower or
                "timestamp" in fecha_lower or
                "date" in fecha_lower or
                "time" in fecha_lower
            )
            
            if is_date_column:
                device_name = self._extract_device_name(fecha_col)
                if not device_name:
                    device_name = value_col
                
                device_name = device_name.strip()
                if device_name:
                    # Evitar colisiones
                    original = device_name
                    suffix = 1
                    while device_name in self.device_columns:
                        suffix += 1
                        device_name = f"{original}_{suffix}"
                    
                    self.device_columns[device_name] = (fecha_col, value_col)
            
            i += 2

    def _extract_device_name(self, date_column: str) -> str:
        """Extrae nombre del dispositivo de forma más inteligente"""
        # Limpiar patrones comunes
        clean_name = date_column
        patterns_to_remove = [
            'fecha hora', 'fecha/hora', 'fechahora', 'fecha - hora',
            'fecha', 'hora', 'timestamp', 'date time', 'datetime'
        ]
        
        for pattern in patterns_to_remove:
            clean_name = clean_name.lower().replace(pattern, '')
        
        # Limpiar caracteres especiales y espacios
        clean_name = ' '.join(clean_name.split()).strip()
        
        # Capitalizar si está todo en minúsculas
        if clean_name and clean_name.islower():
            clean_name = clean_name.title()
            
        return clean_name if clean_name else ""

    def get_devices(self):
        return list(self.device_columns.keys())

    def get_values_for_device(self, device_name: str):
        if not self.csv_data:
            raise CSVServiceError("No se ha cargado un CSV.")
        if device_name not in self.device_columns:
            raise CSVServiceError(f"Electrodoméstico '{device_name}' no encontrado.")

        fecha_col, val_col = self.device_columns[device_name]

        try:
            fecha_idx = self.csv_data.columns.index(fecha_col)
            val_idx = self.csv_data.columns.index(val_col)
        except ValueError:
            raise CSVServiceError("Índices de columnas no encontrados en CSV.")

        results = []
        for row in self.csv_data.rows:
            fecha = row[fecha_idx] if fecha_idx < len(row) else ""
            valor = row[val_idx] if val_idx < len(row) else ""
            results.append((fecha, valor))
        return results

    # NUEVOS MÉTODOS DE ANÁLISIS
    def get_device_statistics(self, device_name: str) -> Dict:
        """Calcula estadísticas básicas para un dispositivo"""
        if device_name in self._analysis_cache:
            return self._analysis_cache[device_name]
            
        values = self.get_values_for_device(device_name)
        numeric_values = []
        
        for fecha, valor in values:
            try:
                # Intentar convertir a float, ignorar vacíos
                if valor and valor.strip():
                    num_val = float(valor)
                    numeric_values.append(num_val)
            except (ValueError, TypeError):
                continue
        
        if not numeric_values:
            return {
                "total_registros": len(values),
                "registros_numericos": 0,
                "error": "No hay valores numéricos para analizar"
            }
        
        stats = {
            "total_registros": len(values),
            "registros_numericos": len(numeric_values),
            "consumo_promedio": round(sum(numeric_values) / len(numeric_values), 2),
            "consumo_maximo": round(max(numeric_values), 2),
            "consumo_minimo": round(min(numeric_values), 2),
            "consumo_total": round(sum(numeric_values), 2)
        }
        
        self._analysis_cache[device_name] = stats
        return stats

    def get_all_statistics(self) -> Dict[str, Dict]:
        """Estadísticas para todos los dispositivos"""
        return {
            device: self.get_device_statistics(device)
            for device in self.get_devices()
        }