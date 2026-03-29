import curses
from sesion_terminal import SesionTerminal

class Cuadro:
    def __init__(self, y, x, h, w):
        # Crear cuadro, con tamaño, foco y si lleva terminal
        self.y, self.x = y, x
        self.h, self.w = h, w
        self.win = curses.newwin(h, w, y, x)
        self.win.keypad(True)
        self.dead = False
        self.terminal = None
        self.crear_terminal()
        self.index = None
    
    def crear_terminal(self):
        try:
            self.terminal = SesionTerminal(self.win)
        except Exception as e:
            self.terminal = None
            try:
                self.win.addstr(1, 2, f"Error terminal: {e}")
            except curses.error:
                pass
                
    def move_resize(self, y, x, h, w):
        h = max(3, h)
        w = max(4, w)
        self.y, self.x, self.h, self.w = y, x, h, w
        try:
            self.win = curses.newwin(h, w, y, x)
            self.win.keypad(True)
        except curses.error:
            return

        if self.terminal:
            try:
                self.terminal.set_window(self.win)
            except Exception:
                pass
    
           
    def draw(self, activa=False, index=None):
        if self.dead:
            return
        if self.h < 3 or self.w < 4:
            return
        self.win.erase()

        # Color / estilo del borde
        if activa and curses.has_colors():
            self.win.attron(curses.color_pair(3) | curses.A_BOLD)

        self.win.box()

        if activa and curses.has_colors():
            self.win.attroff(curses.color_pair(3) | curses.A_BOLD)
        
        # Título del cuadro
        titulo = "Terminal"
        if self.terminal and self.terminal.title:
            titulo = self.terminal.title
            
        if index:
            titulo = f"({index}) - {titulo}"
            
        max_titulo = self.w - 4
        titulo = titulo[:max_titulo]
        
        
        try:
            if activa and curses.has_colors():
                self.win.addstr(0, 2, titulo, curses.color_pair(3) | curses.A_BOLD)
            else:
                self.win.addstr(0, 2, titulo)
        except curses.error:
            pass
               
        # Contenido del terminal
        if self.terminal and self.terminal.alive:
            self.terminal.read_and_render()
        elif self.terminal and not self.terminal.alive:
            self.dead = True
            return
        
        # Cursor
        if self.terminal:
            if activa and self.terminal.alive:
                self.terminal.sincroniza_cursor()
            else:
                self.terminal.limpia_cursor()
        
        self.win.noutrefresh()
        
    def send_key(self, ch):
        if self.terminal and self.terminal.alive:
            self.terminal.send_key(ch)
    
    
