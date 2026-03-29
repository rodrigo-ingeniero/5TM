# medidor_cpu.py

import time
try:
    import psutil # Probamos a importar utilidad de medida de % CPU
except Exception:
    psutil = None
    
class MedidorCPU:
    def __init__(self, interval=3):
        self.interval = interval
        self._last_t = 0.0
        self.cpu_total = None
    
    def read(self):
        now = time.monotonic()
        # Devuelve cpu o "None" si no está disponible
        if now - self._last_t < self.interval:
            return self.cpu_total
        self._last_t = now
        
        if psutil:
            try:
                self.cpu_total = psutil.cpu_percent(interval=None)
            except Exception:
                self.cpu_total = None
        else:
            self.cpu_total = None
            
        return self.cpu_total
        
