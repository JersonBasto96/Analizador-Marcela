class CSVData:
    """
    Representa el CSV en memoria:
      - columns: lista de strings
      - rows: lista de listas (cada fila normalizada al largo de columns)
    """
    def __init__(self, columns=None, rows=None):
        self.columns = columns or []
        self.rows = rows or []