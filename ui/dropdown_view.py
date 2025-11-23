import tkinter as tk
from tkinter import ttk

class DropdownView(ttk.Frame):
    """
    Combobox readonly; on_select recibe (selected_value: str)
    """

    def __init__(self, parent, on_select=None, placeholder="Seleccione un dispositivo", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.on_select = on_select
        self.placeholder = placeholder

        self._combobox = ttk.Combobox(self, state="readonly", font=("Arial", 11))
        self._combobox.pack(fill="x", padx=6, pady=6)
        self._combobox.bind("<<ComboboxSelected>>", self._handle_select)
        self._combobox.set(self.placeholder)

    def update_options(self, options):
        if options is None:
            options = []
        self._combobox["values"] = list(options)
        if options:
            self._combobox.set(self.placeholder)
        else:
            self._combobox.set("No hay dispositivos")

    def _handle_select(self, event):
        val = self._combobox.get()
        if self.on_select:
            try:
                self.on_select(val)
            except TypeError:
                self.on_select()

    def get_selected(self):
        return self._combobox.get()