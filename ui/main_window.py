import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from controllers.csv_controller import CSVController
from ui.dropdown_view import DropdownView
from ui.table_view import TableView
from ui.analysis_view import AnalysisView
from services.csv_service import CSVServiceError

class MainWindow:
    def __init__(self):
        self.controller = CSVController()

        self.window = tk.Tk()
        self.window.title("CSV Analyzer Pro - Analizador de Consumo Energético")
        self.window.geometry("1200x700")

        # Crear notebook para pestañas
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Pestaña 1: Visualización de datos
        self.data_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.data_frame, text="📊 Datos")
        
        # Pestaña 2: Análisis
        self.analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_frame, text="📈 Análisis")

        self._setup_data_tab()
        self._setup_analysis_tab()

    def _setup_data_tab(self):
        """Configurar pestaña de visualización de datos"""
        # Frame superior con controles
        top_frame = ttk.Frame(self.data_frame)
        top_frame.pack(fill="x", padx=8, pady=8)

        self.btn_load = ttk.Button(
            top_frame, 
            text="Cargar CSV", 
            command=self.load_csv
        )
        self.btn_load.pack(side="left")

        self.btn_analyze = ttk.Button(
            top_frame,
            text="Actualizar Análisis",
            command=self.update_analysis
        )
        self.btn_analyze.pack(side="left", padx=5)

        ttk.Label(top_frame, text="Electrodoméstico:").pack(side="left", padx=(20, 5))
        
        self.dropdown = DropdownView(top_frame, on_select=self.show_table, placeholder="Seleccione un electrodoméstico")
        self.dropdown.pack(side="left", fill="x", expand=True, padx=8)

        # Tabla de datos
        self.table = TableView(self.data_frame)
        self.table.pack(fill="both", expand=True, padx=8, pady=8)

    def _setup_analysis_tab(self):
        """Configurar pestaña de análisis"""
        self.analysis_view = AnalysisView(self.analysis_frame)
        self.analysis_view.pack(fill="both", expand=True)
        self.analysis_view.on_device_select = self._on_analysis_device_select

    def load_csv(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("CSV", "*.csv"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return

        try:
            self.controller.load_csv(path)
            messagebox.showinfo("Éxito", f"CSV cargado correctamente")
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
        self.analysis_view.update_devices(devices)
        
        # Mostrar primer dispositivo por defecto
        if devices:
            self.dropdown._combobox.set(devices[0])
            self.show_table(devices[0])
            
        # Actualizar análisis automáticamente
        self.update_analysis()

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

        self.table.update_table_multi(columns=["Fecha Hora", device_name], rows=rows)

    def update_analysis(self):
        """Actualizar todas las vistas de análisis"""
        if not self.controller.csv_data:
            messagebox.showwarning("Advertencia", "Primero carga un archivo CSV")
            return
            
        try:
            # Obtener estadísticas generales
            all_stats = self.controller.get_all_statistics()
            self.analysis_view.update_summary(all_stats)
            
            # Actualizar análisis del dispositivo seleccionado
            current_device = self.analysis_view.device_combo.get()
            if current_device:
                device_stats = self.controller.get_device_statistics(current_device)
                self.analysis_view.update_device_analysis(current_device, device_stats)
                
        except Exception as e:
            messagebox.showerror("Error en análisis", f"Error al calcular estadísticas: {e}")

    def _on_analysis_device_select(self, device):
        """Manejar selección de dispositivo en pestaña de análisis"""
        stats = self.controller.get_device_statistics(device)
        self.analysis_view.update_device_analysis(device, stats)

    def run(self):
        self.window.mainloop()