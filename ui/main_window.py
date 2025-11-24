import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog # <--- AGREGADO simpledialog
from controllers.csv_controller import CSVController
from ui.dropdown_view import DropdownView
from ui.table_view import TableView
from ui.analysis_view import AnalysisView, EnergySummaryView

class MainWindow:
    def __init__(self):
        self.controller = CSVController()
        
        # Referencias a inputs dinámicos
        self.entries_ciclos_wd_starts = []
        self.entries_ciclos_we_starts = []
        self.entries_escalones_wd_starts = []
        self.entries_escalones_wd_ends = []
        self.entries_escalones_we_starts = []
        self.entries_escalones_we_ends = []

        self.window = tk.Tk()
        self.window.title("CSV Analyzer Pro - Simulación Semanal")
        self.window.geometry("1400x950")

        self.main_notebook = ttk.Notebook(self.window)
        self.main_notebook.pack(fill="both", expand=True, padx=10, pady=(5, 0))

        self.status_frame = ttk.Frame(self.window, relief=tk.SUNKEN, padding=(5, 2))
        self.status_frame.pack(side="bottom", fill="x")
        self.lbl_status = ttk.Label(self.status_frame, text="Listo", anchor="w")
        self.lbl_status.pack(side="left", fill="x")
        self.progress = ttk.Progressbar(self.status_frame, mode='indeterminate', length=200)

        # Pestañas
        self.tab_hora_exacta = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.tab_hora_exacta, text="⏱️ Hora Exacta")
        self._setup_hora_exacta_view()

        self.tab_casos_especiales = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.tab_casos_especiales, text="🚀 Casos Especiales")
        self._setup_casos_especiales_view()

        self.tab_analisis_potencia = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.tab_analisis_potencia, text="⚡ Análisis de Potencia")
        self._setup_analisis_potencia_view()

        self.tab_analisis_energia = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.tab_analisis_energia, text="🔋 Análisis de Energía")
        self._setup_analisis_energia_view()

    def run_task(self, description, func):
        self.window.config(cursor="watch")
        self.lbl_status.config(text=f"⏳ {description}...")
        self.progress.pack(side="right", padx=10)
        self.progress.start(10)
        self.window.update() 
        try:
            func()
            self.lbl_status.config(text="✅ Listo")
        except Exception as e:
            self.lbl_status.config(text="❌ Error")
            messagebox.showerror("Error", str(e))
        finally:
            self.progress.stop()
            self.progress.pack_forget()
            self.window.config(cursor="")

    # --- SETUP VISTAS ---
    def _setup_hora_exacta_view(self):
        ctrl = ttk.Frame(self.tab_hora_exacta, relief=tk.GROOVE, borderwidth=1)
        ctrl.pack(fill="x", padx=10, pady=10)
        btn = ttk.Button(ctrl, text="📂 Cargar CSV Hora Exacta", 
                         command=lambda: self.run_task("Cargando archivo", lambda: self.load_csv_generic('hora_exacta', self.dd_hora, self.table_hora)))
        btn.pack(side="left", padx=10, pady=10)
        ttk.Separator(ctrl, orient="vertical").pack(side="left", fill="y", padx=10, pady=5)
        ttk.Label(ctrl, text="Dispositivo:").pack(side="left")
        self.dd_hora = DropdownView(ctrl, on_select=lambda dev: self.show_table_dual('hora_exacta', dev, self.table_hora))
        self.dd_hora.pack(side="left", fill="x", expand=True, padx=10)
        self.table_hora = TableView(self.tab_hora_exacta)
        self.table_hora.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_casos_especiales_view(self):
        header = ttk.Frame(self.tab_casos_especiales, relief=tk.RAISED, borderwidth=1)
        header.pack(fill="x", side="top")
        ttk.Label(header, text="Configuración Global", font=("Arial", 10, "bold")).pack(side="top", pady=5)
        self.sub_notebook = ttk.Notebook(self.tab_casos_especiales)
        self.sub_notebook.pack(fill="both", expand=True, padx=10, pady=10)
        self.sub_ciclos = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.sub_ciclos, text="🔄 Ciclos (Semanal)")
        self._setup_ciclos_view_weekly()
        self.sub_escalones = ttk.Frame(self.sub_notebook)
        self.sub_notebook.add(self.sub_escalones, text="📈 Escalones (Semanal)")
        self._setup_escalones_view_weekly()

    def _setup_ciclos_view_weekly(self):
        parent = self.sub_ciclos
        load_f = ttk.Frame(parent)
        load_f.pack(fill="x", padx=5, pady=5)
        btn_load = ttk.Button(load_f, text="📂 Cargar CSV Ciclos", command=lambda: self.run_task("Cargando CSV", lambda: self._load_csv_dynamic('ciclos')))
        btn_load.pack(side="left")
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Label(ctrl, text="Dispositivo:").pack(side="left")
        self.dd_ciclos = DropdownView(ctrl, placeholder="Seleccione...", on_select=self._on_ciclos_device_select)
        self.dd_ciclos.pack(side="left", fill="x", expand=True, padx=10)
        btn_save = ttk.Button(ctrl, text="✅ Guardar Configuración Semanal", command=lambda: self.run_task("Procesando", self._apply_ciclos_weekly))
        btn_save.pack(side="right", padx=10)
        self.nb_ciclos_config = ttk.Notebook(parent)
        self.nb_ciclos_config.pack(fill="x", padx=5, pady=5)
        self.tab_ciclos_wd = ttk.Frame(self.nb_ciclos_config)
        self.nb_ciclos_config.add(self.tab_ciclos_wd, text="📅 Lunes - Viernes")
        self._setup_ciclos_week_panel(self.tab_ciclos_wd, "wd")
        self.tab_ciclos_we = ttk.Frame(self.nb_ciclos_config)
        self.nb_ciclos_config.add(self.tab_ciclos_we, text="🎉 Sábado - Domingo")
        self._setup_ciclos_week_panel(self.tab_ciclos_we, "we")
        self.table_ciclos = TableView(parent)
        self.table_ciclos.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_ciclos_week_panel(self, parent, prefix):
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Label(ctrl, text="N° Usos:").pack(side="left")
        spin = ttk.Spinbox(ctrl, from_=0, to=10, width=3)
        spin.set(1)
        spin.pack(side="left", padx=5)
        ttk.Button(ctrl, text="Generar", command=lambda: self._gen_ciclos_inputs(prefix, spin.get())).pack(side="left", padx=5)
        frame_inputs = ttk.LabelFrame(parent, text="Horarios Inicio")
        frame_inputs.pack(fill="x", padx=5, pady=5)
        setattr(self, f"spin_ciclos_{prefix}", spin)
        setattr(self, f"frame_ciclos_{prefix}", frame_inputs)

    def _setup_escalones_view_weekly(self):
        parent = self.sub_escalones
        load_f = ttk.Frame(parent)
        load_f.pack(fill="x", padx=5, pady=5)
        btn_load = ttk.Button(load_f, text="📂 Cargar CSV Escalones", command=lambda: self.run_task("Cargando CSV", lambda: self._load_csv_dynamic('escalones')))
        btn_load.pack(side="left")
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Label(ctrl, text="Dispositivo:").pack(side="left")
        self.dd_escalones = DropdownView(ctrl, placeholder="Seleccione...", on_select=self._on_escalones_device_select)
        self.dd_escalones.pack(side="left", fill="x", expand=True, padx=10)
        btn_save = ttk.Button(ctrl, text="✅ Guardar Configuración Semanal", command=lambda: self.run_task("Calculando", self._apply_escalones_weekly))
        btn_save.pack(side="right", padx=10)
        self.nb_escalones_config = ttk.Notebook(parent)
        self.nb_escalones_config.pack(fill="x", padx=5, pady=5)
        self.tab_esc_wd = ttk.Frame(self.nb_escalones_config)
        self.nb_escalones_config.add(self.tab_esc_wd, text="📅 Lunes - Viernes")
        self._setup_escalones_week_panel(self.tab_esc_wd, "wd")
        self.tab_esc_we = ttk.Frame(self.nb_escalones_config)
        self.nb_escalones_config.add(self.tab_esc_we, text="🎉 Sábado - Domingo")
        self._setup_escalones_week_panel(self.tab_esc_we, "we")
        self.table_escalones = TableView(parent)
        self.table_escalones.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_escalones_week_panel(self, parent, prefix):
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Label(ctrl, text="N° Intervalos:").pack(side="left")
        spin = ttk.Spinbox(ctrl, from_=0, to=10, width=3)
        spin.set(1)
        spin.pack(side="left", padx=5)
        ttk.Button(ctrl, text="Generar", command=lambda: self._gen_escalones_inputs(prefix, spin.get())).pack(side="left", padx=5)
        frame_inputs = ttk.LabelFrame(parent, text="Horarios (Inicio - Fin)")
        frame_inputs.pack(fill="x", padx=5, pady=5)
        setattr(self, f"spin_escalones_{prefix}", spin)
        setattr(self, f"frame_escalones_{prefix}", frame_inputs)

    def _setup_analisis_potencia_view(self):
        self.view_potencia = AnalysisView(self.tab_analisis_potencia, controller=self.controller, y_label="Potencia (Watts)", title_prefix="Potencia")
        self.view_potencia.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_analisis_energia_view(self):
        container = ttk.Frame(self.tab_analisis_energia)
        container.pack(fill="both", expand=True)
        
        toolbar = ttk.Frame(container, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(fill="x", side="top", padx=5, pady=5)
        
        # BOTÓN EXPORTAR
        btn_export = ttk.Button(toolbar, text="💾 Exportar Reporte Excel", command=self.export_excel)
        btn_export.pack(side="right", padx=10, pady=5)
        
        self.view_energia = EnergySummaryView(container, controller=self.controller)
        self.view_energia.pack(fill="both", expand=True, padx=10, pady=10)

    # --- EXPORTACIÓN ACTUALIZADA ---
    def export_excel(self):
        # 1. Pedir Código de la Casa
        house_code = simpledialog.askstring("Exportar Reporte", "Ingrese el Código de la Casa:")
        
        # Si cancela o lo deja vacío, salimos o usamos default
        if house_code is None: return # Cancelado
        if not house_code.strip(): house_code = "Reporte_Energia"
        
        # Limpiar caracteres raros del nombre
        safe_name = "".join(c for c in house_code if c.isalnum() or c in (' ', '-', '_')).strip()
        default_filename = f"{safe_name}.xlsx"
        
        # 2. Abrir diálogo de guardado con el nombre pre-llenado
        path = filedialog.asksaveasfilename(
            initialfile=default_filename, # <--- Aquí está la magia
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            title="Guardar Reporte de Energía"
        )
        
        if not path: return
        
        # Recolectar Figuras de la vista de Energía
        figures = {}
        if hasattr(self, 'view_energia'):
            if hasattr(self.view_energia, 'fig_pie'):
                figures['Diagrama Torta'] = self.view_energia.fig_pie
            if hasattr(self.view_energia, 'fig_pareto'):
                figures['Diagrama Pareto'] = self.view_energia.fig_pareto

        def _do_export():
            self.controller.export_report(path, figures)
            
        self.run_task(f"Generando {safe_name}...", _do_export)

    # --- LÓGICA DE CARGA ---
    def load_csv_generic(self, k, d, t):
        self.controller.load_csv(filedialog.askopenfilename(filetypes=[("CSV", "*.csv")]), k)
        devs = self.controller.get_devices(k)
        d.update_options(devs)
        self._refresh_analytics(k)
        if devs: 
            d._combobox.set(devs[0])
            self.show_table_dual(k, devs[0], t)

    def _load_csv_dynamic(self, key):
        path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not path: return
        self.controller.load_csv(path, key)
        devs = self.controller.get_devices(key)
        dd = self.dd_ciclos if key == 'ciclos' else self.dd_escalones
        dd.update_options(devs)
        self._refresh_analytics(key)
        if devs: 
            dd._combobox.set(devs[0])
            if key == 'ciclos': self._on_ciclos_device_select(devs[0])
            else: self._on_escalones_device_select(devs[0])

    def _refresh_analytics(self, key):
        devs = self.controller.get_devices(key)
        if hasattr(self, 'view_potencia'): 
            self.view_potencia.update_devices(key, devs)
        if hasattr(self, 'view_energia'):
            self.view_energia.refresh_tables()
            if hasattr(self.view_energia, 'refresh_monthly_charts'):
                self.view_energia.refresh_monthly_charts()

    def show_table_dual(self, key_context, device_name, table_widget):
        if not device_name or not table_widget: return
        rows = self.controller.get_dual_table_data(key_context, device_name)
        cols = ["Hora / Fecha", "Valor (Lun-Vie)", "Valor (Sáb-Dom)"]
        table_widget.update_table_multi(columns=cols, rows=rows)
        if self.controller.last_warning: messagebox.showwarning("Aviso", self.controller.last_warning)

    # --- CICLOS ---
    def _on_ciclos_device_select(self, dev):
        if not dev: return
        cfg = self.controller.get_device_config('ciclos', dev)
        wd = cfg.get('weekday', {'count': 1, 'starts': ["00:00"]}) if cfg.get('type') == 'weekly' else {'count': 1, 'starts': ["00:00"]}
        self.spin_ciclos_wd.set(wd['count'])
        self._gen_ciclos_inputs("wd", wd['count'], wd['starts'])
        we = cfg.get('weekend', {'count': 1, 'starts': ["00:00"]}) if cfg.get('type') == 'weekly' else {'count': 1, 'starts': ["00:00"]}
        self.spin_ciclos_we.set(we['count'])
        self._gen_ciclos_inputs("we", we['count'], we['starts'])

    def _gen_ciclos_inputs(self, prefix, count, starts=None):
        try: c = int(count)
        except: return
        if not starts: starts = ["00:00"] * c
        frame = getattr(self, f"frame_ciclos_{prefix}")
        for w in frame.winfo_children(): w.destroy()
        new_starts = []
        for i in range(c):
            f = ttk.Frame(frame)
            f.grid(row=i//6, column=i%6, padx=5, pady=5)
            ttk.Label(f, text=f"#{i+1}:").pack(side="left")
            e = ttk.Entry(f, width=6)
            e.insert(0, starts[i] if i < len(starts) else "00:00")
            e.pack(side="left")
            new_starts.append(e)
        if prefix == "wd": self.entries_ciclos_wd_starts = new_starts
        else: self.entries_ciclos_we_starts = new_starts

    def _apply_ciclos_weekly(self):
        dev = self.dd_ciclos.get_selected()
        if not dev or dev == "Seleccione...": return
        wd_s = [e.get() for e in self.entries_ciclos_wd_starts]
        we_s = [e.get() for e in self.entries_ciclos_we_starts]
        self.controller.set_device_config_weekly('ciclos', dev, len(wd_s), wd_s, [], len(we_s), we_s, [])
        self.show_table_dual('ciclos', dev, self.table_ciclos)
        self._refresh_analytics('ciclos')

    # --- ESCALONES ---
    def _on_escalones_device_select(self, dev):
        if not dev: return
        cfg = self.controller.get_device_config('escalones', dev)
        wd = cfg.get('weekday', {'count': 1, 'starts': ["18:00"], 'ends': ["22:00"]})
        self.spin_escalones_wd.set(wd['count'])
        self._gen_escalones_inputs("wd", wd['count'], wd['starts'], wd['ends'])
        we = cfg.get('weekend', {'count': 1, 'starts': ["10:00"], 'ends': ["14:00"]})
        self.spin_escalones_we.set(we['count'])
        self._gen_escalones_inputs("we", we['count'], we['starts'], we['ends'])

    def _gen_escalones_inputs(self, prefix, count, starts=None, ends=None):
        try: c = int(count)
        except: return
        if not starts: starts = ["00:00"] * c
        if not ends: ends = ["01:00"] * c
        frame = getattr(self, f"frame_escalones_{prefix}")
        for w in frame.winfo_children(): w.destroy()
        new_starts, new_ends = [], []
        for i in range(c):
            f = ttk.Frame(frame)
            f.grid(row=i//3, column=i%3, padx=10, pady=5)
            ttk.Label(f, text=f"#{i+1} Ini:").pack(side="left")
            es = ttk.Entry(f, width=6)
            es.insert(0, starts[i] if i < len(starts) else "00:00")
            es.pack(side="left", padx=2)
            ttk.Label(f, text="Fin:").pack(side="left")
            ee = ttk.Entry(f, width=6)
            ee.insert(0, ends[i] if i < len(ends) else "01:00")
            ee.pack(side="left", padx=2)
            new_starts.append(es)
            new_ends.append(ee)
        if prefix == "wd":
            self.entries_escalones_wd_starts = new_starts
            self.entries_escalones_wd_ends = new_ends
        else:
            self.entries_escalones_we_starts = new_starts
            self.entries_escalones_we_ends = new_ends

    def _apply_escalones_weekly(self):
        dev = self.dd_escalones.get_selected()
        if not dev or dev == "Seleccione...": return
        wd_s = [e.get() for e in self.entries_escalones_wd_starts]
        wd_e = [e.get() for e in self.entries_escalones_wd_ends]
        we_s = [e.get() for e in self.entries_escalones_we_starts]
        we_e = [e.get() for e in self.entries_escalones_we_ends]
        self.controller.set_device_config_weekly('escalones', dev, len(wd_s), wd_s, wd_e, len(we_s), we_s, we_e)
        self.show_table_dual('escalones', dev, self.table_escalones)
        self._refresh_analytics('escalones')

    def run(self): self.window.mainloop()