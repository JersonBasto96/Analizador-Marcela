# ui/main_window.py
import tkinter as tk
from tkinter import filedialog, messagebox
from controllers.csv_controller import CSVController
from ui.dropdown_view import DropdownView
from ui.table_view import TableView
from services.csv_service import CSVServiceError

class MainWindow:
    def __init__(self):
        self.controller = CSVController()

        self.window = tk.Tk()
        self.window.title("CSV Viewer App")
        self.window.geometry("900x600")

        top_frame = tk.Frame(self.window)
        top_frame.pack(fill="x", padx=8, pady=8)

        self.btn_load = tk.Button(top_frame, text="Cargar CSV", command=self.load_csv, font=("Arial", 11))
        self.btn_load.pack(side="left")

        self.dropdown = DropdownView(top_frame, on_select=self.show_table, placeholder="Seleccione un electrodoméstico")
        self.dropdown.pack(side="left", fill="x", expand=True, padx=8)

        self.table = TableView(self.window)
        self.table.pack(fill="both", expand=True, padx=8, pady=8)

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path:
            return

        try:
            self.controller.load_csv(path)
        except CSVServiceError as e:
            messagebox.showerror("Error al cargar CSV", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))
            return

        devices = self.controller.get_devices()
        if not devices:
            messagebox.showerror("Error", "No se detectaron electrodomésticos en el CSV.")
            return

        self.dropdown.update_options(devices)

    def show_table(self, device_name):
        if not device_name:
            return
        try:
            rows = self.controller.get_values_for_device(device_name)
        except CSVServiceError as e:
            messagebox.showerror("Error", str(e))
            return
        except Exception as e:
            messagebox.showerror("Error inesperado", str(e))
            return

        # Mostrar en la tabla con encabezados "Fecha Hora" y nombre del dispositivo
        self.table.update_table_multi(columns=["Fecha Hora", device_name], rows=rows)

    def run(self):
        self.window.mainloop()
