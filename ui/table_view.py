# ui/table_view.py
import tkinter as tk
from tkinter import ttk

class TableView(ttk.Frame):
    """
    Treeview con scrollbars.
    update_table_multi(columns, rows) espera:
      - columns: ['Fecha Hora', 'DeviceName']
      - rows: iterable de tuplas/lists [(fecha, valor), ...]
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self._tree = ttk.Treeview(self, show="headings")
        self._tree.pack(side="left", fill="both", expand=True)

        self._scroll_y = ttk.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._scroll_y.pack(side="right", fill="y")
        self._tree.configure(yscrollcommand=self._scroll_y.set)

        self._scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._scroll_x.pack(side="bottom", fill="x")
        self._tree.configure(xscrollcommand=self._scroll_x.set)

    def clear(self):
        # limpiar columnas y filas
        for r in self._tree.get_children():
            self._tree.delete(r)
        self._tree["columns"] = ()

    def update_table_multi(self, columns, rows):
        self.clear()
        if not columns:
            self._tree["columns"] = ("Mensaje",)
            self._tree.heading("Mensaje", text="Sin columnas")
            return

        self._tree["columns"] = tuple(columns)
        for col in columns:
            self._tree.heading(col, text=col)
            self._tree.column(col, anchor="w", width=180)

        if not rows:
            self._tree.insert("", "end", values=tuple([""] * len(columns)))
            return

        for row in rows:
            # row es (fecha, valor)
            safe = []
            for i in range(len(columns)):
                if i < len(row):
                    safe.append("" if row[i] is None else str(row[i]))
                else:
                    safe.append("")
            self._tree.insert("", "end", values=tuple(safe))
