import tkinter as tk
from tkinter import ttk

class TableView(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", pady=(0, 5))
        ttk.Label(control_frame, text="Buscar:").pack(side="left", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search)
        self.clear_search_btn = ttk.Button(control_frame, text="Limpiar", command=self._clear_search)
        self.clear_search_btn.pack(side="left")
        self.status_label = ttk.Label(control_frame, text="")
        self.status_label.pack(side="right")
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True)
        self._tree = ttk.Treeview(tree_frame, show="headings")
        self._tree.pack(side="left", fill="both", expand=True)
        self._scroll_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._scroll_y.pack(side="right", fill="y")
        self._tree.configure(yscrollcommand=self._scroll_y.set)
        self._scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self._tree.xview)
        self._scroll_x.pack(side="bottom", fill="x")
        self._tree.configure(xscrollcommand=self._scroll_x.set)
        self._all_data = []
        self._current_columns = []

    def _on_search(self, event=None):
        search_term = self.search_var.get().lower()
        if not search_term:
            self._display_data(self._all_data)
            self.status_label.config(text=f"Mostrando todos los {len(self._all_data)} registros")
            return
        filtered_data = []
        for row in self._all_data:
            if any(search_term in str(cell).lower() for cell in row):
                filtered_data.append(row)
        self._display_data(filtered_data)
        self.status_label.config(text=f"Mostrando {len(filtered_data)} de {len(self._all_data)} registros")

    def _clear_search(self):
        self.search_var.set("")
        self._display_data(self._all_data)
        self.status_label.config(text=f"Mostrando todos los {len(self._all_data)} registros")

    def _display_data(self, data):
        self.clear()
        if not self._current_columns: return
        self._tree["columns"] = tuple(self._current_columns)
        for col in self._current_columns:
            self._tree.heading(col, text=col)
            self._tree.column(col, anchor="w", width=180)
        for row in data:
            safe_row = []
            for i in range(len(self._current_columns)):
                if i < len(row): safe_row.append("" if row[i] is None else str(row[i]))
                else: safe_row.append("")
            self._tree.insert("", "end", values=tuple(safe_row))

    def clear(self):
        for r in self._tree.get_children(): self._tree.delete(r)
        self._tree["columns"] = ()

    def update_table_multi(self, columns, rows):
        self._current_columns = columns
        self._all_data = rows
        self.clear()
        if not columns: return
        self._tree["columns"] = tuple(columns)
        for col in columns:
            self._tree.heading(col, text=col)
            self._tree.column(col, anchor="w", width=180)
        if not rows: return
        for row in rows:
            safe = []
            for i in range(len(columns)):
                if i < len(row): safe.append("" if row[i] is None else str(row[i]))
                else: safe.append("")
            self._tree.insert("", "end", values=tuple(safe))
        self.status_label.config(text=f"Total: {len(rows)} registros")
        self._all_data = rows