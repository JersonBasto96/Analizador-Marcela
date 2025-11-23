import tkinter as tk
from tkinter import ttk
from typing import Dict

class AnalysisView(ttk.Frame):
    """Vista para mostrar análisis estadísticos"""
    
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Pestaña de resumen
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Resumen General")
        
        # Pestaña por dispositivo
        self.device_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.device_frame, text="Por Dispositivo")
        
        self._setup_summary_tab()
        self._setup_device_tab()
        
    def _setup_summary_tab(self):
        """Configurar pestaña de resumen general"""
        self.summary_text = tk.Text(self.summary_frame, wrap="word", height=15, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(self.summary_frame, command=self.summary_text.yview)
        self.summary_text.configure(yscrollcommand=scrollbar.set)
        
        self.summary_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
    def _setup_device_tab(self):
        """Configurar pestaña de análisis por dispositivo"""
        # Frame para selección
        selection_frame = ttk.Frame(self.device_frame)
        selection_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Dispositivo:").pack(side="left")
        
        self.device_combo = ttk.Combobox(selection_frame, state="readonly", font=("Arial", 10))
        self.device_combo.pack(side="left", fill="x", expand=True, padx=5)
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_select)
        
        # Área de resultados
        self.device_text = tk.Text(self.device_frame, wrap="word", height=12, font=("Arial", 10))
        scrollbar = ttk.Scrollbar(self.device_frame, command=self.device_text.yview)
        self.device_text.configure(yscrollcommand=scrollbar.set)
        
        self.device_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
    def update_devices(self, devices: list):
        """Actualizar lista de dispositivos disponibles"""
        self.device_combo["values"] = devices
        if devices:
            self.device_combo.set(devices[0])
            
    def update_summary(self, statistics: Dict):
        """Actualizar resumen general"""
        self.summary_text.delete(1.0, tk.END)
        
        if not statistics:
            self.summary_text.insert(1.0, "No hay datos para mostrar")
            return
            
        text = "=== RESUMEN GENERAL ===\n\n"
        for device, stats in statistics.items():
            text += f"📊 {device}:\n"
            if "error" in stats:
                text += f"   ❌ {stats['error']}\n"
            else:
                text += f"   • Registros totales: {stats['total_registros']}\n"
                text += f"   • Registros numéricos: {stats['registros_numericos']}\n"
                text += f"   • Consumo promedio: {stats['consumo_promedio']:.2f}\n"
                text += f"   • Consumo máximo: {stats['consumo_maximo']:.2f}\n"
                text += f"   • Consumo mínimo: {stats['consumo_minimo']:.2f}\n"
                text += f"   • Consumo total: {stats['consumo_total']:.2f}\n"
            text += "\n"
            
        self.summary_text.insert(1.0, text)
        
    def update_device_analysis(self, device: str, statistics: Dict):
        """Actualizar análisis de dispositivo específico"""
        self.device_text.delete(1.0, tk.END)
        
        if not statistics or "error" in statistics:
            self.device_text.insert(1.0, f"No hay datos analíticos para {device}")
            return
            
        text = f"=== ANÁLISIS DETALLADO: {device} ===\n\n"
        text += f"📈 Métricas de Consumo:\n"
        text += f"   • Consumo Promedio: {statistics['consumo_promedio']:.2f}\n"
        text += f"   • Consumo Máximo: {statistics['consumo_maximo']:.2f}\n"
        text += f"   • Consumo Mínimo: {statistics['consumo_minimo']:.2f}\n"
        text += f"   • Consumo Total: {statistics['consumo_total']:.2f}\n\n"
        
        text += f"📊 Estadísticas de Datos:\n"
        text += f"   • Registros Totales: {statistics['total_registros']}\n"
        text += f"   • Registros Numéricos: {statistics['registros_numericos']}\n"
        non_numeric = statistics['total_registros'] - statistics['registros_numericos']
        text += f"   • Registros No Numéricos: {non_numeric}\n"
        
        self.device_text.insert(1.0, text)
        
    def _on_device_select(self, event):
        """Manejar selección de dispositivo"""
        device = self.device_combo.get()
        if device and hasattr(self, "on_device_select"):
            self.on_device_select(device)