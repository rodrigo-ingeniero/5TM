
# Terminal embebida en una ventana de curses:
# - Crea PTY (emular terminal) y lanza /bin/zsh o /bin/bash
# - Usa la librería pyte para interpretar las secuencias ANSI y renderizar la terminal en una ventana curses sin bordes
# - Dibuja texto dentro del interior de la ventana dentro de los bordes (encapsular)

import os
import pty
import fcntl
import termios
import struct
import selectors
import signal
import subprocess
import curses
from pyte import modes as mo


# Emulador de terminal
try:
    import pyte
except Exception:
    pyte = None
    
class SesionTerminal:
    # Lanza un shell en PTY y dibuja su pantalla en una ventana curses usando pyte.
    # Funciona en MacOS y Linux (POSIX), para Windows habría que hacer algo distinto
    
    def __init__(self, win, shell=None):
        """
        win : ventana curses donde dibujar la terminal (área interior del box)
        shell : ruta del shell (por defecto zsh si existe, sino bash)
        """
        
        if shell is None:
            shell = "/bin/zsh" if os.path.exists("/bin/zsh") else "/bin/bash"
            
        self.win = win
        
        if os.path.exists("/bin/zsh"):
            self.shell = "/bin/zsh"
        else:
            self.shell = shell
        self.alive = True
        
        # Tamaño interior sin bordes, en líneas y columnas
        rows, cols = self._inner_size()
        
        # Emulador de pantalla
        #self.screen.reset_mode(mo.DECAWM) # Desactivar Auto-Wrap
        self.screen = pyte.Screen(179,41) # Extraño, pero parece que funciona y no se rompe
        self.stream = pyte.Stream(self.screen, strict = False)
        #self.screen = pyte.Screen(cols,rows)
                
        self.title = "Terminal"
        
        # Crear PTY
        # Mantener 'slave_fd' abierto para poder cambiar el tamaño con ioctl.
        self.master_fd, self.slave_fd = pty.openpty()
        
        # Ajustar tamaño de la tty esclava
        self._set_winsize(self.slave_fd, rows, cols)
        
        # Master no bloqueante
        fl = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        
        # Fork: hijo ejecuta shell; padre gestiona el PTY
        self.child_pid = os.fork()
        
        if self.child_pid == 0:
        	# ----- Proceso hijo -----
            os.setsid()  # nueva sesión
            
            # La tty esclava como controlling terminal
            fcntl.ioctl(self.slave_fd, termios.TIOCSCTTY, 0)
            
            # Señales por defecto
            signal.signal(signal.SIGINT, signal.SIG_DFL)
            signal.signal(signal.SIGTSTP, signal.SIG_DFL)
            signal.signal(signal.SIGQUIT, signal.SIG_DFL)
            
            # Conectar la tty esclava como stdin/stdout/stderr
            os.dup2(self.slave_fd, 0)
            os.dup2(self.slave_fd, 1)
            os.dup2(self.slave_fd, 2)
            
            # TERM moderno
            os.environ["TERM"] = "xterm-256color"

            # Cerrar el master en el hijo
            os.close(self.master_fd)
            # Ejecutar el shell
            os.execlp(self.shell, self.shell, "-i")
            # Si llega aquí, falló
            os._exit(1)
        else:
            # ----- Proceso padre -----
            self.alive = True
            
        # ----------------- utilidades internas -----------------
    def _inner_size(self):
        """Devuelve (rows, cols) útiles dentro del box (márgenes de 1)."""
        h, w = self.win.getmaxyx()  # h=rows (alto), w=cols (ancho) con bordes
        rows = max(1, h - 2)
        cols = max(1, w - 2)
        return rows, cols
        
    def _set_winsize(self, fd, rows, cols):
    	"""ioctl TIOCSWINSZ para que el shell conozca el tamaño (rows, cols)."""
    	fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        
    def _cleanup_fds(self):
        for fd in (self.master_fd, self.slave_fd):
            try:
                os.close(fd)
            except Exception:
                pass
                           
    def _fg_process_name(self):
        try:
            pgid = os.tcgetpgrp(self.master_fd)
            out = subprocess.check_output(
                ["ps", "-p", str(pgid), "-o", "comm="],text=True).strip()
            argums = subprocess.check_output(
                ["ps", "-p", str(pgid), "-o", "args="],text=True).strip()
            if out:
                self.title = out
                if argums:
                    self.title = argums
        except Exception:
            pass
        
    # ----------------- Métodos públicas -----------------
    def get_inner_size(self):
        return self._inner_size()
        
    def get_ioctl_winsize(self):  
        data = fcntl.ioctl(self.slave_fd, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
        alto, ancho, pixelsX, pixelsY = struct.unpack("HHHH", data)
        return ancho, alto
        
    def send_key(self, ch):
        """Convierte tecla curses en bytes y los escribe al PTY (shell)."""
    	# ASCII sencillo
        if 0 <= ch <= 255:
            b = bytes([ch])
            if ch in (10,13):
                os.write(self.master_fd, b"\r")
            else:
                os.write(self.master_fd, b)
        
        # Teclas especiales a secuencias ANSI
        mapping = {
        	# Flechas
        	260: b"\x1b[D",  # KEY_LEFT
        	261: b"\x1b[C",  # KEY_RIGHT
        	259: b"\x1b[A",  # KEY_UP
        	258: b"\x1b[B",  # KEY_DOWN
        	# Home/End
        	262: b"\x1b[H",  # KEY_HOME
        	360: b"\x1b[F",  # KEY_END
        	# PageUp/PageDown
        	339: b"\x1b[5~", # KEY_PPAGE
        	338: b"\x1b[6~", # KEY_NPAGE
        	# Delete/Insert/Backspace (varía según terminal; ajusta si hiciera falta)
        	330: b"\x1b[3~", # KEY_DC (Delete)
        	331: b"\x1b[2~", # KEY_IC (Insert)
        	263: b"\x7f",	# KEY_BACKSPACE → DEL
    	}
        seq = mapping.get(ch)
        if seq:
            os.write(self.master_fd, seq)

    def resize(self):
        """Redimensiona el emulador y notifica el nuevo tamaño al shell (SIGWINCH)."""
        if not self.alive:
            return
        rows, cols = self._inner_size()
        try:
            self._set_winsize(self.slave_fd, rows, cols)
        except OSError:
            self.alive = False
            return
        self.screen.resize(rows,cols)
        try:
            os.kill(self.child_pid, signal.SIGWINCH)
        except Exception:
            pass
            
    def set_window(self, win):
        self.win = win
        self.resize()
        self.read_and_render()
              
    def read_and_render(self):
        """Lee datos del PTY, alimenta pyte y dibuja dentro del interior de la ventana."""
        # Leer todo lo disponible
        while True:
            try:
                data = os.read(self.master_fd, 4096)
            except BlockingIOError:
                break
            except OSError:
                self.alive = False
                break
            if not data:
                # EOF
                self.alive = False
                self._cleanup_fds()
                break
            # Decodificar y alimentar emulador
            self.stream.feed(data.decode("utf-8", "replace"))
            
        if self.screen.title:
            self.title = self.screen.title.strip()
        else:
            proc = self._fg_process_name()
            if proc:
                self.title = proc
        if self.title == "/bin/zsh" or self.title == "/bin/zsh -i":
            self.title = "Terminal"
        try:
            ancho, alto = self.get_ioctl_winsize()
        except:
            ancho = 0
            alto = 0
        #self.title += " " + str(ancho) + "x" + str(alto) # Debug
        
        # Render en el interior (márgenes +1)
        rows, cols = self._inner_size()
        # Limpia área interior
        for r in range(rows):
            try:
                self.win.addstr(r + 1, 1, " " * cols)
            except Exception:
                pass
        # Dibuja líneas de display (solo texto; atributos de color requieren lógica extra)
        for i, line in enumerate(self.screen.display[:rows]):
            try:
                self.win.addstr(i + 1, 1, line)
            except Exception:
                pass

    
    def sincroniza_cursor(self):
        cy = self.screen.cursor.y + 1
        cx = self.screen.cursor.x + 1
        rows, cols = self._inner_size()
        
        if 0 <= cy < rows + 1 and 0 <= cx < cols + 1:
            try:
                self.win.addstr(cy,cx,"█")
                pass
            except curses.error:
                pass
                
    def limpia_cursor(self):
        cy = self.screen.cursor.y + 1
        cx = self.screen.cursor.x + 1
        rows, cols = self._inner_size()
        
        if 0 <= cy < rows + 1 and 0 <= cx < cols + 1:
            try:
                self.win.addstr(cy,cx,"")
            except curses.error:
                pass
        
    def terminate(self):
        """Termina la sesión del shell."""
        if not self.alive:
            return
        try:
            os.kill(self.child_pid, signal.SIGTERM)
        except Exception:
            pass
        self.alive = False
        # No cerramos master/slave explícitamente aquí; el GC limpiará al salir de la app.

    