import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import timedelta
from ui.table_view import TableView

# ========================================================
#  CLASE 1: VISTA DE GRÁFICAS (POTENCIA)
# ========================================================
class AnalysisView(ttk.Frame):
    def __init__(self, parent, controller=None, y_label="Potencia (Watts)", title_prefix="Consumo", *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller
        self.y_label = y_label
        self.title_prefix = title_prefix
        self.is_energy = "Energía" in title_prefix
        
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
        ctrl = ttk.Frame(parent)
        ctrl.pack(fill="x", padx=5, pady=5)
        
        combo_dev = None
        if key != 'total':
            ttk.Label(ctrl, text="Dispositivo:").pack(side="left")
            combo_dev = ttk.Combobox(ctrl, state="readonly", values=["Todos"], width=15)
            combo_dev.set("Todos")
            combo_dev.pack(side="left", padx=(5, 15))
            combo_dev.bind("<<ComboboxSelected>>", lambda e: self.plot_data(key))

        ttk.Label(ctrl, text="Visualizar:").pack(side="left")
        time_options = ["Semana Completa (7 Días)", "Perfil Entre Semana (24h)", "Perfil Fin de Semana (24h)"]
        combo_period = ttk.Combobox(ctrl, state="readonly", values=time_options, width=25)
        combo_period.set("Semana Completa (7 Días)")
        combo_period.pack(side="left", padx=(5, 15))
        combo_period.bind("<<ComboboxSelected>>", lambda e: self.plot_data(key))

        ttk.Button(ctrl, text="🔄 Actualizar", command=lambda: self.plot_data(key)).pack(side="left")

        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        annot = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w", alpha=0.9), arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)

        def hover(event):
            vis = annot.get_visible()
            if event.inaxes == ax:
                found = False
                for line in ax.lines:
                    cont, ind = line.contains(event)
                    if cont:
                        x, y = line.get_data()
                        idx = ind["ind"][0]
                        x_val = mdates.num2date(x[idx])
                        y_val = y[idx]
                        label = line.get_label()
                        annot.xy = (x[idx], y[idx])
                        sel_per = combo_period.get()
                        is_week = "Completa" in sel_per
                        fmt = "%a %H:%M" if is_week else "%H:%M"
                        annot.set_text(f"{label}\n{x_val.strftime(fmt)}\n{y_val:.2f} {self.y_label.split()[0]}")
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        found = True
                        break
                if not found and vis:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
            elif vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

        canvas.mpl_connect("motion_notify_event", hover)
        return {'fig': fig, 'ax': ax, 'canvas': canvas, 'combo_dev': combo_dev, 'combo_period': combo_period}

    def update_devices(self, key, devs):
        if key in self.tabs and self.tabs[key]['combo_dev']:
            c = self.tabs[key]['combo_dev']
            curr = c.get()
            c['values'] = ["Todos"] + devs
            if curr not in ["Todos"] + devs: c.set("Todos")

    def plot_data(self, key):
        if not self.controller: return
        top = self.winfo_toplevel()
        top.config(cursor="watch")
        top.update_idletasks()
        try:
            tab = self.tabs[key]
            ax = tab['ax']
            sel_dev = tab['combo_dev'].get() if tab['combo_dev'] else "Todos"
            sel_per = tab['combo_period'].get()
            ax.clear()
            ax.set_ylabel(self.y_label)
            ax.grid(True, linestyle='--', alpha=0.5)
            
            is_weekly = "Completa" in sel_per
            day_type = 'weekday' if "Entre Semana" in sel_per else 'weekend'

            if is_weekly:
                ax.set_xlabel("Día")
                ax.xaxis.set_major_locator(mdates.DayLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%a'))
            else:
                ax.set_xlabel("Hora")
                ax.xaxis.set_major_locator(mdates.MinuteLocator(byminute=[0, 30]))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
                plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

            plots = 0
            def plot_one(t, y, l, c=None):
                if t:
                    ax.plot(t, y, label=l, color=c, linewidth=1.5, picker=5)
                    if key=='total': ax.fill_between(t, y, alpha=0.1, color=c)
                    return 1
                return 0

            if key == 'total':
                if is_weekly: t, y = self.controller.get_total_weekly_vector(self.is_energy)
                else: t, y = self.controller.get_total_typical_profile(day_type, self.is_energy)
                plots += plot_one(t, y, "Total", 'green' if self.is_energy else 'black')
                ax.set_title(f"{self.title_prefix} Total - {sel_per}")
            else:
                devs = self.controller.get_devices(key)
                if sel_dev and sel_dev != "Todos": devs = [d for d in devs if d == sel_dev]
                for d in devs:
                    if is_weekly: t, y = self.controller.get_weekly_power_vector(key, d)
                    else: t, y = self.controller.get_typical_day_profile(key, d, day_type)
                    if self.is_energy and y:
                        e_vec, acc = [], 0
                        fac = 1.0/60000.0
                        for val in y:
                            acc += val * fac
                            e_vec.append(acc)
                        y = e_vec
                    plots += plot_one(t, y, d)
                ax.set_title(f"{self.title_prefix}: {key.title()}")

            if plots > 0:
                ax.legend(loc='upper left', fontsize='small')
                if is_weekly: tab['fig'].autofmt_xdate()
            else: ax.text(0.5, 0.5, "Sin datos", ha='center')
            tab['canvas'].draw()
        finally: top.config(cursor="")

# ========================================================
#  CLASE 2: VISTA DE TABLAS (ENERGÍA) + FACTURA
# ========================================================
class EnergySummaryView(ttk.Frame):
    def __init__(self, parent, controller=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.controller = controller
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tab_weekly = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_weekly, text="📅 Resumen Semanal")
        self._setup_weekly_tab()
        
        self.tab_monthly_main = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_monthly_main, text="📆 Proyección Mensual")
        self._setup_monthly_main_structure()

        self.tab_bill = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_bill, text="🧾 Factura Comparativa")
        self._setup_bill_tab()

    def _setup_weekly_tab(self):
        ctrl = ttk.Frame(self.tab_weekly)
        ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Button(ctrl, text="🔄 Recalcular", command=self.refresh_tables).pack(side="right")
        ttk.Label(ctrl, text="Detalle de Energía (kWh)", font=("Arial", 11, "bold")).pack(side="left")
        self.table_weekly = TableView(self.tab_weekly)
        self.table_weekly.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_monthly_main_structure(self):
        self.nb_monthly = ttk.Notebook(self.tab_monthly_main)
        self.nb_monthly.pack(fill="both", expand=True, padx=5, pady=5)
        self.sub_monthly_data = ttk.Frame(self.nb_monthly)
        self.nb_monthly.add(self.sub_monthly_data, text="📋 Datos (Pareto)")
        self._setup_monthly_data_tab()
        self.sub_monthly_charts = ttk.Frame(self.nb_monthly)
        self.nb_monthly.add(self.sub_monthly_charts, text="📊 Gráficas de Análisis")
        self._setup_monthly_charts_tab()

    def _setup_monthly_data_tab(self):
        ctrl = ttk.Frame(self.sub_monthly_data)
        ctrl.pack(fill="x", padx=5, pady=5)
        ttk.Button(ctrl, text="🔄 Recalcular", command=self.refresh_tables).pack(side="right")
        ttk.Label(ctrl, text="Tabla de Análisis ABC (Pareto)", font=("Arial", 11, "bold")).pack(side="left")
        self.table_monthly = TableView(self.sub_monthly_data)
        self.table_monthly.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_monthly_charts_tab(self):
        canvas_container = tk.Canvas(self.sub_monthly_charts)
        scrollbar = ttk.Scrollbar(self.sub_monthly_charts, orient="vertical", command=canvas_container.yview)
        self.scrollable_frame = ttk.Frame(canvas_container)
        self.scrollable_frame.bind("<Configure>", lambda e: canvas_container.configure(scrollregion=canvas_container.bbox("all")))
        canvas_container.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas_container.configure(yscrollcommand=scrollbar.set)
        canvas_container.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        ttk.Button(self.scrollable_frame, text="🔄 Actualizar Gráficas", command=self.refresh_monthly_charts).pack(pady=5)
        
        self.fig_pie, self.ax_pie = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas_pie = FigureCanvasTkAgg(self.fig_pie, master=self.scrollable_frame)
        self.canvas_pie.get_tk_widget().pack(fill="x", expand=True, padx=10, pady=10)
        
        self.fig_pareto, self.ax_pareto = plt.subplots(figsize=(7, 5), dpi=100)
        self.canvas_pareto = FigureCanvasTkAgg(self.fig_pareto, master=self.scrollable_frame)
        self.canvas_pareto.get_tk_widget().pack(fill="x", expand=True, padx=10, pady=10)

    def _setup_bill_tab(self):
        container = ttk.Frame(self.tab_bill)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        lbl_calc = ttk.Label(container, text="Energía Total Calculada (Mes):", font=("Arial", 12))
        lbl_calc.grid(row=0, column=0, sticky="w", pady=10)
        self.var_calculated_total = tk.StringVar(value="0.00")
        lbl_val_calc = ttk.Label(container, textvariable=self.var_calculated_total, font=("Arial", 12, "bold"))
        lbl_val_calc.grid(row=0, column=1, sticky="w", padx=10)
        ttk.Label(container, text="kWh").grid(row=0, column=2, sticky="w")
        lbl_input = ttk.Label(container, text="Energía Factura Real (Mes):", font=("Arial", 12))
        lbl_input.grid(row=1, column=0, sticky="w", pady=10)
        self.ent_bill_input = ttk.Entry(container, font=("Arial", 11))
        self.ent_bill_input.grid(row=1, column=1, sticky="w", padx=10)
        ttk.Label(container, text="kWh").grid(row=1, column=2, sticky="w")
        btn_calc = ttk.Button(container, text="Calcular Diferencia", command=self.calculate_bill_diff)
        btn_calc.grid(row=2, column=0, columnspan=3, pady=20)
        self.lbl_diff_kwh = ttk.Label(container, text="Diferencia: --- kWh", font=("Arial", 11))
        self.lbl_diff_kwh.grid(row=3, column=0, columnspan=3, sticky="w", pady=5)
        self.lbl_diff_perc = ttk.Label(container, text="Porcentaje de Error: --- %", font=("Arial", 11))
        self.lbl_diff_perc.grid(row=4, column=0, columnspan=3, sticky="w", pady=5)
        self.lbl_verdict = ttk.Label(container, text="", font=("Arial", 11, "bold"))
        self.lbl_verdict.grid(row=5, column=0, columnspan=3, sticky="w", pady=10)

    def refresh_tables(self):
        self.refresh_weekly()
        self.refresh_monthly_data()
        self.refresh_monthly_charts()
        self.refresh_bill_data()

    def refresh_weekly(self):
        if not self.controller: return
        try:
            rows_data, totals = self.controller.get_energy_summary()
            ui_rows = []
            for item in rows_data:
                ui_rows.append([
                    item['section'], item['device'],
                    f"{item['daily_wd']:.4f}", f"{item['daily_we']:.4f}",
                    f"{item['total_5d']:.4f}", f"{item['total_2d']:.4f}", f"{item['total_week']:.4f}"
                ])
            ui_rows.append(["", "--- TOTAL ---", f"{totals['daily_wd']:.4f}", f"{totals['daily_we']:.4f}", f"{totals['total_5d']:.4f}", f"{totals['total_2d']:.4f}", f"{totals['total_week']:.4f}"])
            cols = ["Sección", "Dispositivo", "24h (L-V)", "24h (S-D)", "Total L-V", "Total S-D", "TOTAL SEMANA"]
            self.table_weekly.update_table_multi(cols, ui_rows)
        except Exception as e: print(f"Error weekly: {e}")

    def refresh_monthly_data(self):
        if not self.controller: return
        if not hasattr(self.controller, 'get_monthly_projection'): return
        try:
            rows, grand_total = self.controller.get_monthly_projection()
            ui_rows = []
            for item in rows:
                ui_rows.append([
                    item['device'],
                    f"{item['kwh_month']:.4f}",
                    f"{item['rel_energy']:.2f}%",
                    f"{item['acc_kwh']:.4f}",
                    f"{item['acc_rel']:.2f}%"
                ])
            ui_rows.append(["--- TOTAL ---", f"{grand_total:.4f}", "100.00%", f"{grand_total:.4f}", "100.00%"])
            cols = ["Dispositivo", "Energía (kWh/mes)", "Energía Relativa", "Energía Acumulada", "Relativa Acumulada"]
            self.table_monthly.update_table_multi(cols, ui_rows)
        except Exception as e: print(f"Error monthly data: {e}")

    def refresh_monthly_charts(self):
        if not self.controller: return
        if not hasattr(self.controller, 'get_monthly_projection'): return
        
        try:
            rows, grand_total = self.controller.get_monthly_projection()
            if not rows: return
            labels = [r['device'] for r in rows]
            values_kwh = [r['kwh_month'] for r in rows]
            values_rel = [r['rel_energy'] for r in rows]
            values_acc_rel = [r['acc_rel'] for r in rows]

            # TORTA
            self.ax_pie.clear()
            wedges, texts, autotexts = self.ax_pie.pie(
                values_rel, labels=None, autopct='%1.1f%%', startangle=90, pctdistance=0.85, textprops={'fontsize': 8}
            )
            self.ax_pie.set_title("Distribución de Energía (%)")
            legend_labels = [f"{l} ({v:.1f}%)" for l, v in zip(labels, values_rel)]
            self.ax_pie.legend(wedges, legend_labels, title="Dispositivos", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize='small')
            self.fig_pie.tight_layout()
            self.canvas_pie.draw()

            # PARETO
            self.ax_pareto.clear()
            if hasattr(self, 'ax2'): self.ax_pareto.figure.delaxes(self.ax2)
            self.ax2 = self.ax_pareto.twinx()
            x_pos = range(len(labels))
            self.ax_pareto.bar(x_pos, values_kwh, color='skyblue', label='Consumo (kWh)', align='center')
            self.ax2.plot(x_pos, values_acc_rel, color='red', marker='o', markersize=5, linewidth=2, label='% Acumulado', zorder=10)
            
            self.ax_pareto.set_ylim(0, grand_total * 1.1)
            self.ax2.set_ylim(0, 110)
            
            self.ax_pareto.set_xticks(x_pos)
            self.ax_pareto.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
            self.ax_pareto.set_ylabel("Energía (kWh/mes)")
            self.ax2.set_ylabel("Porcentaje Acumulado (%)")
            self.ax2.axhline(y=80, color='green', linestyle='--', alpha=0.5, linewidth=1)
            
            lines_1, labels_1 = self.ax_pareto.get_legend_handles_labels()
            lines_2, labels_2 = self.ax2.get_legend_handles_labels()
            self.ax_pareto.legend(lines_1 + lines_2, labels_1 + labels_2, loc='center right', fontsize='small')
            self.ax_pareto.set_title("Diagrama de Pareto")
            self.fig_pareto.subplots_adjust(bottom=0.25, right=0.9)
            self.canvas_pareto.draw()
        except Exception as e: print(f"Error charts: {e}")

    def refresh_bill_data(self):
        if not self.controller: return
        try:
            if hasattr(self.controller, 'get_monthly_projection'):
                _, grand_total = self.controller.get_monthly_projection()
                self.var_calculated_total.set(f"{grand_total:.2f}")
        except: pass

    def calculate_bill_diff(self):
        try:
            calc = float(self.var_calculated_total.get())
            bill = float(self.ent_bill_input.get())
            
            # CAMBIO: Valor absoluto en la diferencia también
            diff = abs(calc - bill)
            perc = (diff / bill * 100) if bill > 0 else 0.0
            
            self.lbl_diff_kwh.config(text=f"Diferencia: {diff:.2f} kWh") # Sin signo
            self.lbl_diff_perc.config(text=f"Desviación: {perc:.2f} %")
            
            if perc <= 10: self.lbl_verdict.config(text="✅ La simulación es PRECISA (<10%)", foreground="green")
            elif perc <= 20: self.lbl_verdict.config(text="⚠️ La simulación es ACEPTABLE (<20%)", foreground="orange")
            else: self.lbl_verdict.config(text="❌ Alta Desviación: Revise parámetros", foreground="red")
        except ValueError: self.lbl_verdict.config(text="Ingrese un número válido", foreground="red")