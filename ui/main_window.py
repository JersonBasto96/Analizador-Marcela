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
        
        self.entries_ciclos_starts = []
        self.entries_escalones_starts = []
        self.entries_escalones_ends = []

        self.window = tk.Tk()
        self.window.title("CSV Analyzer Pro - Multi Contexto")
        self.window.geometry("1350x900")

        self.main_notebook = ttk.Notebook(self.window)
        self.main_notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. PESTAÑA HORA EXACTA
        self.tab_hora_exacta = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.tab_hora_exacta, text="⏱️ Hora Exacta")
        self._setup_hora_exacta_view()

        # 2. PESTAÑA CASOS ESPECIALES
        self.tab_casos_especiales = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.tab_casos_especiales, text="🚀 Casos Especiales")
        self._setup_casos_especiales_view()

        # 3. PESTAÑA ANÁLISIS DE POTENCIA (Renombrada)
        self.tab_analisis_potencia = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.tab_analisis_potencia, text="⚡ Análisis de Potencia")
        self._setup_analisis_potencia_view()

        # 4. PESTAÑA ANÁLISIS DE ENERGÍA (Nueva)
        self.tab_analisis_energia = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.tab_analisis_energia, text="🔋 Análisis de Energía")
        self._setup_analisis_energia_view()

    # --- SETUP VISTAS ---
    
    def _setup_hora_exacta_view(self):
        # (Sin cambios - igual que antes)
        ctrl_frame = ttk.Frame(self.tab_hora_exacta, relief=tk.GROOVE, borderwidth=1)
        ctrl_frame.pack(fill="x", padx=10, pady=10)
        btn = ttk.Button(ctrl_frame, text="📂 Cargar CSV Hora Exacta", 
                         command=lambda: self.load_csv_generic('hora_exacta', self.dd_hora, self.table_hora))
        btn.pack(side="left", padx=10, pady=10)
        ttk.Separator(ctrl_frame, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        ttk.Label(ctrl_frame, text="Dispositivo:").pack(side="left")
        self.dd_hora = DropdownView(ctrl_frame, on_select=lambda dev: self.show_table('hora_exacta', dev, self.table_hora))
        self.dd_hora.pack(side="left", fill="x", expand=True, padx=10)
        self.table_hora = TableView(self.tab_hora_exacta)
        self.table_hora.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_casos_especiales_view(self):
        # (Sin cambios - igual que antes)
        header = ttk.Frame(self.tab_casos_especiales, relief=tk.RAISED, borderwidth=1)
        header.pack(fill="x", side="top")
        ttk.Label(header, text="Configuración Global", font=("Arial", 10, "bold")).pack(side="top", pady=5)
        self.sub_notebook = ttk.Notebook(self.tab_casos_especiales)
        self.sub_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.sub_ciclos = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.sub_ciclos, text="🔄 Ciclos")
        self._setup_sub_dynamic('ciclos')
        self.sub_escalones = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.sub_escalones, text="📈 Escalones")
        self._setup_sub_dynamic('escalones')

    def _setup_sub_dynamic(self, context_key):
        # (Sin cambios - igual que antes)
        parent = self.sub_ciclos if context_key == 'ciclos' else self.sub_escalones
        load_frame = ttk.Frame(parent)
        load_frame.pack(fill="x", padx=5, pady=5)
        btn = ttk.Button(load_frame, text=f"📂 Cargar CSV {context_key.title()}", 
                         command=lambda: self._load_csv_dynamic(context_key))
        btn.pack(side="left")
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Label(ctrl, text="Dispositivo:").pack(side="left")
        dd = DropdownView(ctrl, placeholder="Seleccione...", 
                          on_select=lambda dev: self._on_dynamic_device_select(context_key, dev))
        dd.pack(side="left", fill="x", expand=True, padx=(5, 15))
        ttk.Label(ctrl, text="N° Intervalos:").pack(side="left")
        spin = ttk.Spinbox(ctrl, from_=1, to=10, width=3)
        spin.set(1)
        spin.pack(side="left", padx=5)
        ttk.Button(ctrl, text="Generar Inputs", 
                   command=lambda: self._generate_inputs(context_key, spin.get())).pack(side="left", padx=5)
        ttk.Button(ctrl, text="✅ Aplicar", 
                   command=lambda: self._apply_dynamic_changes(context_key)).pack(side="left", padx=(15, 5))
        frame_dyn = ttk.LabelFrame(parent, text="Configuración de Horarios")
        frame_dyn.pack(fill="x", padx=10, pady=5)
        table = TableView(parent)
        table.pack(fill="both", expand=True, padx=5, pady=5)
        setattr(self, f"dd_{context_key}", dd)
        setattr(self, f"spin_{context_key}", spin)
        setattr(self, f"frame_dyn_{context_key}", frame_dyn)
        setattr(self, f"table_{context_key}", table)

    # --- NUEVAS VISTAS DE ANÁLISIS ---

    def _setup_analisis_potencia_view(self):
        """Configura la vista de Potencia (W)"""
        self.view_potencia = AnalysisView(self.tab_analisis_potencia, controller=self.controller, 
                                          y_label="Potencia (Watts)", title_prefix="Potencia")
        self.view_potencia.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_analisis_energia_view(self):
        """Configura la vista de Energía (kWh)"""
        # Nota: Por ahora graficará datos de potencia hasta que agreguemos la lógica de integración
        self.view_energia = AnalysisView(self.tab_analisis_energia, controller=self.controller, 
                                         y_label="Energía (kWh)", title_prefix="Energía")
        self.view_energia.pack(fill="both", expand=True, padx=10, pady=10)

    # --- LÓGICA DE ACTUALIZACIÓN GRÁFICA ---

    def _refresh_all_analytics(self, context_key=None):
        """Helper para refrescar ambas pestañas de análisis"""
        devices = self.controller.get_devices(context_key) if context_key else []
        
        # 1. Refrescar Potencia
        if hasattr(self, 'view_potencia'):
            if context_key:
                self.view_potencia.update_devices(context_key, devices)
                self.view_potencia.plot_data(context_key)
            # También actualizar el total si estamos cargando datos
            self.view_potencia.plot_data('total')

        # 2. Refrescar Energía
        if hasattr(self, 'view_energia'):
            if context_key:
                self.view_energia.update_devices(context_key, devices)
                self.view_energia.plot_data(context_key)
            self.view_energia.plot_data('total')

    # --- CARGA Y EVENTOS ---

    def load_csv_generic(self, k, d, t):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return
        try:
            self.controller.load_csv(path, k)
            messagebox.showinfo("Info", "Cargado")
            devs = self.controller.get_devices(k)
            d.update_options(devs)
            
            # Actualizamos gráficas
            self._refresh_all_analytics(k)

            if devs: 
                d._combobox.set(devs[0])
                self.show_table(k, devs[0], t)
        except Exception as e: messagebox.showerror("Error", str(e))

    def _load_csv_dynamic(self, context_key):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return
        try:
            self.controller.load_csv(path, context_key)
            messagebox.showinfo("Éxito", "Archivo cargado.")
            
            devices = self.controller.get_devices(context_key)
            dd = getattr(self, f"dd_{context_key}")
            dd.update_options(devices)
            
            # Actualizamos gráficas
            self._refresh_all_analytics(context_key)

            if devices:
                dd._combobox.set(devices[0])
                self._on_dynamic_device_select(context_key, devices[0])
        except Exception as e: messagebox.showerror("Error", str(e))

    def _apply_dynamic_changes(self, context_key):
        dd = getattr(self, f"dd_{context_key}")
        device = dd.get_selected()
        if not device or device == "Seleccione...": return
        
        if context_key == 'ciclos':
            starts = [e.get() for e in self.entries_ciclos_starts]
            ends = []
        else:
            starts = [e.get() for e in self.entries_escalones_starts]
            ends = [e.get() for e in self.entries_escalones_ends]

        try:
            self.controller.set_device_config(context_key, device, len(starts), starts, ends)
            rows = self.controller.get_values_for_device(context_key, device, start_times=starts, end_times=ends)
            getattr(self, f"table_{context_key}").update_table_multi(["Fecha", device], rows)
            
            # Actualizamos gráficas tras aplicar cambios
            self._refresh_all_analytics(context_key)
                
        except Exception as e: print(e)

    # --- RESTO DE MÉTODOS AUXILIARES ---
    def _on_dynamic_device_select(self, context_key, device):
        if not device: return
        config = self.controller.get_device_config(context_key, device)
        count = config.get('count', 1)
        starts = config.get('starts', ["00:00"])
        ends = config.get('ends', ["01:00"])
        getattr(self, f"spin_{context_key}").set(count)
        self._create_inputs_ui(context_key, count, starts, ends)
        self._apply_dynamic_changes(context_key)

    def _generate_inputs(self, context_key, count_str):
        try: count = int(count_str)
        except: return
        self._create_inputs_ui(context_key, count, ["00:00"]*count, ["01:00"]*count)

    def _create_inputs_ui(self, context_key, count, starts, ends):
        frame = getattr(self, f"frame_dyn_{context_key}")
        for w in frame.winfo_children(): w.destroy()
        new_starts = []
        new_ends = []
        for i in range(count):
            s_val = starts[i] if i < len(starts) else "00:00"
            e_val = ends[i] if i < len(ends) else "01:00"
            c = ttk.Frame(frame)
            c.grid(row=i//3, column=i%3, padx=10, pady=5, sticky="w")
            ttk.Label(c, text=f"#{i+1} Inicio:").pack(side="left")
            es = ttk.Entry(c, width=6)
            es.insert(0, s_val)
            es.pack(side="left", padx=(2, 10))
            new_starts.append(es)
            if context_key == 'escalones':
                ttk.Label(c, text="Fin:").pack(side="left")
                ee = ttk.Entry(c, width=6)
                ee.insert(0, e_val)
                ee.pack(side="left", padx=2)
                new_ends.append(ee)
        if context_key == 'ciclos': self.entries_ciclos_starts = new_starts
        else:
            self.entries_escalones_starts = new_starts
            self.entries_escalones_ends = new_ends

    def show_table(self, k, d, t):
        if not d: return
        try: t.update_table_multi(["Fecha", d], self.controller.get_values_for_device(k, d))
        except: pass

    def run(self): self.window.mainloop()