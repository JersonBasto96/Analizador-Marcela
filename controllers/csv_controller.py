# controllers/csv_controller.py
from services.csv_service import CSVService, CSVServiceError
from models.csv_model import CSVData

class CSVController:
    """
    Controlador que orquesta lectura y parseo semántico del CSV.
    Detecta pares: "Fecha Hora <Device>"  +  "<Device>"
    """

    def __init__(self):
        self.csv_data: CSVData | None = None
        # device_name -> (fecha_col_name, value_col_name)
        self.device_columns = {}

    def load_csv(self, path: str):
        try:
            self.csv_data = CSVService.read_csv(path)
        except CSVServiceError:
            raise
        except Exception as e:
            raise CSVServiceError(f"Error inesperado al leer CSV: {e}")

        if not self.csv_data.columns:
            raise CSVServiceError("CSV sin encabezados.")

        # validar paridad de columnas (idealmente pares, pero no fatal)
        if len(self.csv_data.columns) < 2:
            raise CSVServiceError("El CSV no tiene suficientes columnas.")

        # parsear dispositivos
        self._parse_device_pairs()

        if not self.device_columns:
            raise CSVServiceError("No se encontraron pares válidos 'Fecha Hora' + 'Device' en encabezados.")

        return self.csv_data

    def _parse_device_pairs(self):
        """
        Recorre columnas de 2 en 2 y detecta si la primera del par contiene 'fecha' o 'hora'.
        Si es así, extrae el nombre del dispositivo (por heurística) y registra el par.
        """
        self.device_columns = {}
        cols = self.csv_data.columns

        # Recorremos en pares: 0-1,2-3,...
        i = 0
        while i + 1 < len(cols):
            fecha_col = cols[i]
            value_col = cols[i + 1]

            # Comprobación flexible: la columna de fecha debe contener la palabra 'fecha' o 'hora' (insensible)
            if ("fecha" in fecha_col.lower()) or ("hora" in fecha_col.lower()):
                # intentar extraer nombre: quitar prefijo "Fecha Hora" u variantes
                # Ej: "Fecha Hora Airfryer" -> "Airfryer"
                fc = fecha_col
                # quitar "Fecha Hora", "FechaHora", "Fecha", "Hora" con limpieza
                possible = fc.replace("Fecha Hora", "").replace("Fecha/Hora","").replace("FechaHora","")\
                             .replace("Fecha - Hora","").replace("Fecha","").replace("Hora","").strip()
                device_name = possible if possible else value_col

                device_name = device_name.strip()
                if device_name:
                    # Evitar colisiones: si ya existe, ampliar sufijo numérico
                    original = device_name
                    suffix = 1
                    while device_name in self.device_columns:
                        suffix += 1
                        device_name = f"{original}_{suffix}"

                    self.device_columns[device_name] = (fecha_col, value_col)
            # avanzar al siguiente par
            i += 2

    def get_devices(self):
        return list(self.device_columns.keys())

    def get_values_for_device(self, device_name: str):
        if not self.csv_data:
            raise CSVServiceError("No se ha cargado un CSV.")
        if device_name not in self.device_columns:
            raise CSVServiceError(f"Electrodoméstico '{device_name}' no encontrado.")

        fecha_col, val_col = self.device_columns[device_name]

        # obtener índices en columnas originales
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
