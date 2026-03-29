"""
estado_red.py

Clase EstadoRed multiplataforma (Linux/macOS) para obtener estado de red:
- Conectividad a Internet (TCP a 1.1.1.1:53)
- Interfaz por defecto (Linux: /proc/net/route, macOS: route -n get default)
- IP de la interfaz (Linux: ip -4 addr show, macOS: ipconfig getifaddr)
- SSID opcional (Linux: iwgetid -r, macOS: networksetup -getairportnetwork)

Incluye un hilo opcional para refresco periódico no bloqueante.
"""
import platform
import socket
import subprocess
import threading
import time
from typing import Optional, Tuple

class EstadoRed:
    def __init__(self, include_ssid: bool = False, refresh_interval: float = 3.0):
        self.include_ssid = include_ssid
        self.refresh_interval = max(0.5, float(refresh_interval))
        self.system = platform.system()
        # Estado interno
        self.online: bool = False
        self.iface: Optional[str] = None
        self.ip: Optional[str] = None
        self.ssid: Optional[str] = None
        # Concurrencia
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------ API pública ------------------
    def start(self):
        """Arranca el hilo de actualización periódica."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run_loop, name="EstadoRedLoop", daemon=True)
        self._thread.start()

    def stop(self):
        """Detiene el hilo si está corriendo."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def refresh_now(self):
        """Actualiza el estado inmediatamente (sin hilo)."""
        online, iface, ip, ssid = self._compute_status()
        with self._lock:
            self.online, self.iface, self.ip, self.ssid = online, iface, ip, ssid

    def snapshot(self) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """Devuelve una tupla con el último estado (thread-safe)."""
        with self._lock:
            return self.online, self.iface, self.ip, self.ssid

    # ------------------ Loop interno ------------------
    def _run_loop(self):
        while not self._stop.is_set():
            try:
                online, iface, ip, ssid = self._compute_status()
                with self._lock:
                    self.online, self.iface, self.ip, self.ssid = online, iface, ip, ssid
            except Exception:
                # Evita que el hilo muera por errores puntuales
                pass
            finally:
                self._stop.wait(self.refresh_interval)

    # ------------------ Cálculo del estado ------------------
    def _compute_status(self) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        iface = self._get_default_interface()
        ip = self._get_interface_ip(iface) if iface else None
        online = self._has_internet()
        ssid = self._get_wifi_ssid(iface) if (self.include_ssid and iface) else None
        return online, iface, ip, ssid

    # ------------------ Utilidades por sistema ------------------
    def _has_internet(self, timeout: float = 0.8) -> bool:
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=timeout).close()
            return True
        except OSError:
            return False

    def _get_default_interface(self) -> Optional[str]:
        if self.system == "Darwin":
            return self._mac_default_interface()
        elif self.system == "Linux":
            return self._linux_default_interface()
        return None

    def _get_interface_ip(self, iface: str) -> Optional[str]:
        if self.system == "Darwin":
            return self._mac_iface_ip(iface)
        elif self.system == "Linux":
            return self._linux_iface_ip(iface)
        return None

    def _get_wifi_ssid(self, iface: str) -> Optional[str]:
        if self.system == "Darwin":
            return self._mac_wifi_ssid(iface)
        elif self.system == "Linux":
            return self._linux_wifi_ssid(iface)
        return None

    # ----------- Linux -----------
    def _linux_default_interface(self) -> Optional[str]:
        try:
            with open("/proc/net/route") as f:
                for line in f.readlines()[1:]:
                    parts = line.strip().split()
                    iface, dest, flags = parts[0], parts[1], int(parts[3], 16)
                    if dest == '00000000' and (flags & 2):  # RTF_GATEWAY
                        return iface
        except Exception:
            pass
        return None

    def _linux_iface_ip(self, iface: str) -> Optional[str]:
        try:
            out = subprocess.check_output(["ip", "-4", "addr", "show", iface], text=True)
            for line in out.splitlines():
                line = line.strip()
                if line.startswith("inet "):
                    return line.split()[1].split("/")[0]
        except Exception:
            pass
        return None

    def _linux_wifi_ssid(self, iface: str) -> Optional[str]:
        try:
            ssid = subprocess.check_output(["iwgetid", "-r"], text=True).strip()
            return ssid or None
        except Exception:
            return None

    # ----------- macOS -----------
    def _mac_default_interface(self) -> Optional[str]:
        try:
            salida = subprocess.check_output(
                ["route", "-n", "get", "default"], 
                text = True, stderr=subprocess.DEVNULL, timeout = 0.8
            )
            #out = subprocess.check_output(["route", "-n", "get", "default"], text=True)
            for line in salida.splitlines():
                line = line.strip()
                if line.startswith("interface:"):
                    return line.split()[-1]
        except Exception:
            pass
        return None

    def _mac_iface_ip(self, iface: str) -> Optional[str]:
        try:
            ip = subprocess.check_output(
                ["ipconfig", "getifaddr", iface], 
                text=True, stderr=subprocess.DEVNULL,timeout=0.6
                ).strip()
            return ip or None
        except Exception:
            return None

    def _mac_wifi_ssid(self, iface: str) -> Optional[str]:
        try:
            out = subprocess.check_output(
                ["networksetup", "-getairportnetwork", iface], 
                text=True, stderr=subprocess.DEVNULL, timeout=0.6
                ).strip()
            if ": " in out:
                return out.split(": ", 1)[1] or None
        except Exception:
            pass
        return None

