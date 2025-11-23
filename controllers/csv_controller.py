from services.csv_service import CSVService, CSVServiceError
from models.csv_model import CSVData
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta, time

class CSVContext:
    def __init__(self):
        self.data: CSVData | None = None
        self.device_columns: Dict = {}
        self.analysis_cache: Dict = {}
        self.device_configs: Dict[str, Dict[str, Any]] = {}

class CSVController:
    def __init__(self):
        self.contexts: Dict[str, CSVContext] = {
            'hora_exacta': CSVContext(),
            'general': CSVContext(),
            'ciclos': CSVContext(),
            'escalones': CSVContext()
        }
        self.last_warning: str | None = None
        self.VOLTAGE = 120.0  # Constante de conversión

    # --- GESTIÓN DE MEMORIA ---
    def set_device_config(self, context_key: str, device_name: str, count: int, starts: List[str], ends: List[str] = None):
        if context_key in self.contexts:
            self.contexts[context_key].device_configs[device_name] = {
                'count': count,
                'starts': starts,
                'ends': ends or []
            }

    def get_device_config(self, context_key: str, device_name: str) -> Dict[str, Any]:
        if context_key in self.contexts:
            return self.contexts[context_key].device_configs.get(device_name, {
                'count': 1, 'starts': ["00:00"], 'ends': ["01:00"]
            })
        return {'count': 1, 'starts': ["00:00"], 'ends': ["01:00"]}

    # --- LECTURA ---
    def load_csv(self, path: str, context_key: str):
        if context_key not in self.contexts: self.contexts[context_key] = CSVContext()
        ctx = self.contexts[context_key]
        try:
            ctx.data = CSVService.read_csv(path)
            ctx.analysis_cache.clear()
            ctx.device_configs.clear()
        except CSVServiceError: raise
        except Exception as e: raise CSVServiceError(f"Error inesperado al leer CSV: {e}")

        if not ctx.data.columns: raise CSVServiceError("CSV sin encabezados.")
        if len(ctx.data.columns) < 1: raise CSVServiceError("El CSV está vacío.")

        self._parse_device_pairs(ctx, context_key)
        if not ctx.device_columns: raise CSVServiceError("No se encontraron dispositivos válidos.")
        return ctx.data

    def _parse_device_pairs(self, ctx: CSVContext, context_key: str):
        ctx.device_columns = {}
        cols = [col.strip() for col in ctx.data.columns]
        i = 0
        pairs_found = False
        while i + 1 < len(cols):
            fecha_col = cols[i]
            value_col = cols[i + 1]
            if "fecha" in fecha_col.lower() or "hora" in fecha_col.lower() or "time" in fecha_col.lower():
                device_name = self._extract_device_name(fecha_col)
                if not device_name: device_name = value_col
                device_name = device_name.strip()
                if device_name:
                    original = device_name
                    suffix = 1
                    while device_name in ctx.device_columns:
                        suffix += 1
                        device_name = f"{original}_{suffix}"
                    ctx.device_columns[device_name] = (fecha_col, value_col)
                    pairs_found = True
            i += 2

        if context_key == 'escalones' and not pairs_found:
            for col in cols:
                if not col: continue
                device_name = col.strip()
                original = device_name
                suffix = 1
                while device_name in ctx.device_columns:
                    suffix += 1
                    device_name = f"{original}_{suffix}"
                ctx.device_columns[device_name] = (None, col)

    def _extract_device_name(self, date_column: str) -> str:
        clean_name = date_column
        patterns = ['fecha hora', 'fecha/hora', 'fechahora', 'fecha', 'hora', 'timestamp']
        for p in patterns: clean_name = clean_name.lower().replace(p, '')
        clean_name = ' '.join(clean_name.split()).strip()
        if clean_name and clean_name.islower(): clean_name = clean_name.title()
        return clean_name if clean_name else ""

    def get_devices(self, context_key: str):
        if context_key in self.contexts: return list(self.contexts[context_key].device_columns.keys())
        return []

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str: return None
        formats = ["%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]
        for fmt in formats:
            try: return datetime.strptime(date_str.strip(), fmt)
            except ValueError: continue
        return None

    # --- OBTENCIÓN DE DATOS RAW ---
    def get_values_for_device(self, context_key: str, device_name: str, start_times: List[str] = None, end_times: List[str] = None) -> List[Tuple[str, str]]:
        self.last_warning = None
        if context_key not in self.contexts or not self.contexts[context_key].data:
            raise CSVServiceError(f"No hay datos cargados en {context_key}.")
        ctx = self.contexts[context_key]
        if device_name not in ctx.device_columns: raise CSVServiceError(f"Dispositivo '{device_name}' no encontrado.")
        fecha_col, val_col = ctx.device_columns[device_name]
        raw_data = []
        nominal_power_str = "0"
        max_val_found = 0.0

        if fecha_col:
            try:
                fecha_idx = ctx.data.columns.index(fecha_col)
                val_idx = ctx.data.columns.index(val_col)
            except ValueError: raise CSVServiceError("Error de índices.")
            for row in ctx.data.rows:
                f_str = row[fecha_idx] if fecha_idx < len(row) else ""
                v_str = row[val_idx] if val_idx < len(row) else ""
                dt = self._parse_date(f_str)
                if dt: raw_data.append((dt, f_str, v_str))
                try:
                    val = float(v_str.replace(',', '.'))
                    if val > max_val_found:
                        max_val_found = val
                        nominal_power_str = v_str
                except: continue
            raw_data.sort(key=lambda x: x[0])
        else:
            try: val_idx = ctx.data.columns.index(val_col)
            except ValueError: raise CSVServiceError("Error de índices.")
            for row in ctx.data.rows:
                if val_idx < len(row):
                    v_str = row[val_idx]
                    try:
                        val = float(v_str.replace(',', '.'))
                        if val > max_val_found:
                            max_val_found = val
                            nominal_power_str = v_str
                    except: continue

        if context_key == 'hora_exacta' and "nevera" in device_name.lower():
            final_data = self._process_nevera_logic(raw_data)
            return [(item[1], item[2]) for item in final_data]
        elif context_key == 'ciclos' and start_times:
            multi_cycle = self._apply_multi_cycle_day(raw_data, start_times)
            return [(item[1], item[2]) for item in multi_cycle]
        elif context_key == 'escalones' and start_times and end_times:
            if raw_data: base_date = raw_data[0][0].date()
            else: base_date = datetime.now().date()
            step_data = self._generate_step_profile(nominal_power_str, base_date, start_times, end_times)
            return [(item[1], item[2]) for item in step_data]
        else:
            return [(item[1], item[2]) for item in raw_data]

    # --- MATEMÁTICA DE POTENCIA (W) Y ENERGÍA (kWh) ---
    
    def get_power_profile_1min(self, context_key: str, device_name: str) -> Tuple[List[datetime], List[float]]:
        """Devuelve vector de POTENCIA (Watts) normalizado a 1 min"""
        config = self.get_device_config(context_key, device_name)
        data_rows = self.get_values_for_device(context_key, device_name, config.get('starts'), config.get('ends'))
        
        if not data_rows: return [], []

        try:
            first_dt = datetime.strptime(data_rows[0][0], "%d/%m/%Y %H:%M:%S")
            base_date = first_dt.date()
        except: base_date = datetime.now().date()

        time_axis = [datetime.combine(base_date, time(0,0)) + timedelta(minutes=i) for i in range(1440)]
        power_axis = [0.0] * 1440
        
        start_of_day = datetime.combine(base_date, time(0,0))
        minute_buckets = {i: [] for i in range(1440)}
        
        for t_str, v_str in data_rows:
            try:
                dt = datetime.strptime(t_str, "%d/%m/%Y %H:%M:%S")
                delta = dt - start_of_day
                minute_idx = int(delta.total_seconds() // 60)
                if 0 <= minute_idx < 1440:
                    val_raw = float(v_str.replace(',', '.'))
                    minute_buckets[minute_idx].append(val_raw)
            except: continue

        for i in range(1440):
            values = minute_buckets[i]
            if values:
                avg_val = sum(values) / len(values)
                
                # --- CORRECCIÓN AQUÍ ---
                # Escalones = Ya es Watts (No multiplicar)
                # Otros = Es Amperios (Multiplicar por 120)
                if context_key == 'escalones':
                    power_axis[i] = avg_val
                else:
                    power_axis[i] = avg_val * self.VOLTAGE
            else:
                power_axis[i] = 0.0

        return time_axis, power_axis

    def get_total_power_vector(self) -> Tuple[List[datetime], List[float]]:
        """Suma de Potencia de todos los dispositivos"""
        total_power = [0.0] * 1440
        time_axis = []
        for ctx_key in ['hora_exacta', 'ciclos', 'escalones']:
            for dev in self.get_devices(ctx_key):
                t_axis, p_axis = self.get_power_profile_1min(ctx_key, dev)
                if not time_axis: time_axis = t_axis
                for i in range(1440):
                    if i < len(p_axis): total_power[i] += p_axis[i]
        
        if not time_axis:
            base = datetime.now().date()
            time_axis = [datetime.combine(base, time(0,0)) + timedelta(minutes=i) for i in range(1440)]
            
        return time_axis, total_power

    def get_energy_profile(self, context_key: str, device_name: str) -> Tuple[List[datetime], List[float]]:
        """Energía Acumulada (kWh)"""
        t_axis, p_axis_watts = self.get_power_profile_1min(context_key, device_name)
        if not t_axis: return [], []

        energy_axis_kwh = [0.0] * 1440
        accumulated_kwh = 0.0
        conversion_factor = 1.0 / 60000.0 # Watts -> kW, Minutos -> Horas (1/1000 * 1/60)

        for i in range(1440):
            instant_kwh = p_axis_watts[i] * conversion_factor
            accumulated_kwh += instant_kwh
            energy_axis_kwh[i] = accumulated_kwh
            
        return t_axis, energy_axis_kwh

    def get_total_energy_vector(self) -> Tuple[List[datetime], List[float]]:
        """Energía Acumulada Total"""
        t_axis, p_axis_total_watts = self.get_total_power_vector()
        if not t_axis: return [], []

        energy_axis_kwh = [0.0] * 1440
        accumulated_kwh = 0.0
        conversion_factor = 1.0 / 60000.0

        for i in range(1440):
            instant_kwh = p_axis_total_watts[i] * conversion_factor
            accumulated_kwh += instant_kwh
            energy_axis_kwh[i] = accumulated_kwh

        return t_axis, energy_axis_kwh

    # --- LÓGICAS INTERNAS ---
    def _generate_step_profile(self, nominal_val_str, base_date, start_times, end_times):
        timeline = []
        current = datetime.combine(base_date, time(0,0))
        end_of_day = current + timedelta(hours=24)
        while current < end_of_day:
            timeline.append({'dt': current, 'str': current.strftime("%d/%m/%Y %H:%M:%S"), 'val': "0"})
            current += timedelta(minutes=1)
        for i in range(len(start_times)):
            if i >= len(end_times): break
            try:
                t_s = datetime.strptime(start_times[i], "%H:%M").time()
                t_e = datetime.strptime(end_times[i], "%H:%M").time()
                dt_s = datetime.combine(base_date, t_s)
                dt_e = datetime.combine(base_date, t_e)
                if dt_e < dt_s: dt_e += timedelta(days=1)
                for point in timeline:
                    if dt_s <= point['dt'] < dt_e: point['val'] = nominal_val_str
            except: continue
        return [(t['dt'], t['str'], t['val']) for t in timeline]

    def _apply_multi_cycle_day(self, raw_data, start_times_str):
        if not raw_data: return []
        target_times = []
        for t in start_times_str:
            try:
                try: tt = datetime.strptime(t, "%H:%M").time()
                except: tt = datetime.strptime(t, "%H:%M:%S").time()
                target_times.append(tt)
            except: continue
        target_times.sort()
        interval = timedelta(minutes=1)
        if len(raw_data) > 1:
            d = raw_data[1][0] - raw_data[0][0]
            if d.total_seconds() > 0: interval = d
        base = raw_data[0][0].date()
        day_s = datetime.combine(base, time(0,0))
        day_e = day_s + timedelta(hours=24)
        final = []
        cursor = day_s
        orig_first = raw_data[0][0]
        for t_t in target_times:
            c_s = datetime.combine(base, t_t)
            while cursor < c_s and (c_s - cursor).total_seconds() > 0:
                final.append((cursor, cursor.strftime("%d/%m/%Y %H:%M:%S"), "0"))
                cursor += interval
            eff_s = max(cursor, c_s)
            offset = eff_s - orig_first
            for dt, _, val in raw_data:
                n_dt = dt + offset
                if n_dt < day_e:
                    if not final or n_dt >= final[-1][0]:
                        final.append((n_dt, n_dt.strftime("%d/%m/%Y %H:%M:%S"), val))
                        cursor = n_dt
            cursor += interval
        while cursor < day_e:
            if not final or cursor > final[-1][0]:
                final.append((cursor, cursor.strftime("%d/%m/%Y %H:%M:%S"), "0"))
            cursor += interval
        return final

    def _process_nevera_logic(self, sorted_data):
        if not sorted_data: return []
        s = sorted_data[0][0]
        e = sorted_data[-1][0]
        if (e-s) < timedelta(hours=24):
            self.last_warning = "⚠️ Advertencia: Ciclo incompleto (<24h)."
            return sorted_data
        target = (s + timedelta(days=1)).date()
        syn = []
        for dt, _, v in sorted_data:
            if dt.date() == target: syn.append((dt, dt.strftime("%d/%m/%Y %H:%M:%S"), v))
            elif dt.date() == s.date():
                s_dt = dt + timedelta(days=1)
                if s_dt.date() == target: syn.append((s_dt, s_dt.strftime("%d/%m/%Y %H:%M:%S"), v))
        syn.sort(key=lambda x: x[0])
        return [x for x in syn if x[0].date() == target]

    def get_device_statistics(self, context_key: str, device_name: str) -> Dict:
        # Estadísticas: Ajustamos para que reflejen el valor real (Watts o Amps según sea el caso)
        # OJO: Aquí las estadísticas actuales calculan sobre el valor CRUDO.
        # Si quieres que las estadísticas también sean en Watts, habría que aplicar la lógica.
        # Por consistencia con la tabla (que muestra el valor 'raw' que viene en el CSV),
        # dejaremos las estadísticas sobre el valor crudo, pero el gráfico sí hace la conversión.
        
        ctx = self.contexts.get(context_key)
        if not ctx or not ctx.data: return {}
        if device_name in ctx.analysis_cache: return ctx.analysis_cache[device_name]
        config = self.get_device_config(context_key, device_name)
        values = self.get_values_for_device(context_key, device_name, config.get('starts'), config.get('ends'))
        numeric = []
        for _, val in values:
            try:
                if val: numeric.append(float(val.replace(',', '.')))
            except: continue
        total = len(values)
        if not numeric: return {"total_registros": total, "registros_numericos": 0, "error": "Sin datos"}
        stats = {
            "total_registros": total, "registros_numericos": len(numeric),
            "consumo_promedio": round(sum(numeric)/len(numeric), 2),
            "consumo_maximo": round(max(numeric), 2), "consumo_minimo": round(min(numeric), 2),
            "consumo_total": round(sum(numeric), 2)
        }
        ctx.analysis_cache[device_name] = stats
        return stats

    def get_all_statistics(self, context_key: str) -> Dict:
        return {dev: self.get_device_statistics(context_key, dev) for dev in self.get_devices(context_key)}