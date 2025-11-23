import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

class AnalysisView(ttk.Frame):
    """
    Vista de Gráficas Inteligente:
    - Detecta si es Potencia o Energía.
    - Llama a los métodos correspondientes del controlador.
    """
    
    def __init__(self, parent, controller=None, y_label="Potencia (Watts)", title_prefix="Consumo", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller
        self.y_label = y_label
        self.title_prefix = title_prefix
        self.is_energy_view = "Energía" in title_prefix # Bandera para saber qué pedir al controlador
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tabs = {}
        for key in ['hora_exacta', 'ciclos', 'escalones', 'total']:
            frame = ttk.Frame(self.notebook)
            title = key.replace('_', ' ').title()
            if key == 'total': title = "📊 TOTAL"
            self.notebook.add(frame, text=title)
            self.tabs[key] = self._setup_graph_tab(frame, key)

    def _setup_graph_tab(self, parent, key):
        ctrl_frame = ttk.Frame(parent)
        ctrl_frame.pack(fill="x", padx=5, pady=5)
        
        device_combo = None
        if key != 'total':
            ttk.Label(ctrl_frame, text="Visualizar:").pack(side="left")
            device_combo = ttk.Combobox(ctrl_frame, state="readonly", values=["Todos"])
            device_combo.set("Todos")
            device_combo.pack(side="left", padx=10)
            device_combo.bind("<<ComboboxSelected>>", lambda e, k=key, c=device_combo: self.plot_data(k, c.get()))

        btn_refresh = ttk.Button(ctrl_frame, text="🔄 Actualizar Gráfica", 
                                 command=lambda k=key, c=device_combo: self.plot_data(k, c.get() if c else None))
        btn_refresh.pack(side="left")

        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        return {'fig': fig, 'ax': ax, 'canvas': canvas, 'combo': device_combo}

    def update_devices(self, context_key, devices_list):
        if context_key in self.tabs and self.tabs[context_key]['combo']:
            combo = self.tabs[context_key]['combo']
            combo['values'] = ["Todos"] + devices_list
            if not combo.get(): combo.set("Todos")

    def plot_data(self, context_key, selected_device="Todos"):
        if not self.controller: return
        
        tab = self.tabs[context_key]
        ax = tab['ax']
        fig = tab['fig']
        canvas = tab['canvas']
        
        ax.clear()
        ax.set_xlabel("Hora del Día")
        ax.set_ylabel(self.y_label)
        ax.grid(True, linestyle='--', alpha=0.6)
        
        locator = mdates.HourLocator(interval=2)
        formatter = mdates.DateFormatter('%H:%M')
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)

        plots_made = 0
        
        # --- LÓGICA DE SELECCIÓN DE DATOS ---
        
        if context_key == 'total':
            # 1. Gráfica TOTAL
            if self.is_energy_view:
                t_axis, y_axis = self.controller.get_total_energy_vector()
                color = 'green'
            else:
                t_axis, y_axis = self.controller.get_total_power_vector()
                color = 'black'
                
            if t_axis:
                ax.plot(t_axis, y_axis, label="Total Vivienda", color=color, linewidth=2)
                ax.fill_between(t_axis, y_axis, alpha=0.2, color=color)
                plots_made += 1
                ax.set_title(f"{self.title_prefix} Total Acumulado" if self.is_energy_view else f"{self.title_prefix} Total Instantánea")
                
        else:
            # 2. Gráficas POR SECCIÓN
            devices = self.controller.get_devices(context_key)
            if selected_device and selected_device != "Todos":
                devices = [d for d in devices if d == selected_device]
            
            for dev in devices:
                if self.is_energy_view:
                    t_axis, y_axis = self.controller.get_energy_profile(context_key, dev)
                else:
                    t_axis, y_axis = self.controller.get_power_profile_1min(context_key, dev)
                    
                if t_axis:
                    ax.plot(t_axis, y_axis, label=dev)
                    plots_made += 1

            ax.set_title(f"{self.title_prefix}: {context_key.replace('_',' ').title()}")

        if plots_made > 0:
            ax.legend(loc='upper left', fontsize='small')
            fig.autofmt_xdate()
        else:
            ax.text(0.5, 0.5, "Sin datos disponibles", ha='center', va='center')

        canvas.draw()