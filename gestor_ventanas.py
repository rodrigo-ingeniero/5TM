import curses
from cuadro import Cuadro
from nodo import NodoVentana, NodoSplit
from animacion import Renderer
from layout import compute_layout, LayoutAnimator, Rect
import time

class GestorVentanas:
    def __init__(self, stdscr):
        # Este gestor es una pantalla en sí, ocupa todo y lleva las otras ventanas
        self.stdscr = stdscr
        self.root = None
        self.activa = None
        self.renderer = Renderer()
        self.animator = LayoutAnimator()
        self.next_id = 1
        self.animar = True
        self.matando = False
        
    def create_initial_window(self):
        alto, ancho = self.stdscr.getmaxyx() 

        # Crear el cuadro y la ventana inicial
        cuadro = Cuadro(0, 0, alto - 3, ancho)
        nodo = NodoVentana(cuadro)

        # Asignar ID único
        nodo.id = str(self.next_id)
        self.next_id += 1

        # Establecer como raíz y ventana activa
        self.root = nodo
        self.activa = nodo
        
    def handle_key(self, ch):
        # Si se pulsa Alt + algo, se consume el comando antes de llegar a la ventana activa
        # Gestión de ventanas
        
        if ch == 162: # Alt + h (split horizontal)
            self._split_activa('h')
            return True

        if ch == 154: # Alt + v (split vertical)
            self._split_activa('v')
            return True

        if ch == 130: # Alt + d (destruir ventana)
            self._cerrar_activa()
            return True
            
        if ch == 171: # Alt + s (pasar foco a siguiente ventana)
            self._siguiente_ventana()
            return True
            
        if ch == 165: # Alt + a (pasar foco a anterior ventana)
            self._anterior_ventana()
            return True    
        
        return False
        
    def _split_activa(self, orientacion):
        hojas = []
        self._recolectar_hojas(self.root, hojas)
        if len(hojas) >= 5:
            return

        if not self.activa:
            return
        
        # --- Layout ANTES del split ---
        x, y, h, w = self._usable_geometry()
        old_layout = compute_layout(self.root, x, y, h, w)

        # --- Cambio estructural REAL ---
        nodo_original = self.activa

        nodo_nuevo = NodoVentana(Cuadro(0, 0, 1, 1))
        nodo_nuevo.id = str(self.next_id)
        self.next_id += 1

        split = NodoSplit(orientacion, nodo_original, nodo_nuevo)

        if self.root == nodo_original:
            self.root = split
        else:
            self._reemplazar_nodo(self.root, nodo_original, split)

        self.activa = nodo_nuevo
        # --- Layout DESPUÉS del split ---
        new_layout = compute_layout(self.root, x, y, h, w)
        
        if self.animar:
            
            # --- Animación (solo marcos) ---
            frames = self.animator.interpolate_create(orientacion, old_layout, new_layout)
        
            for frame in frames:
                self.renderer.render(self.stdscr, frame)
                time.sleep(self.animator.delay)

        # --- Estado final real ---
        self.relayout()

    def _hojas_muertas(self, nodo, out):
        if isinstance(nodo, NodoVentana):
            if nodo.cuadro.dead:
                out.append(nodo)
        elif isinstance(nodo, NodoSplit):
            self._hojas_muertas(nodo.a, out)
            self._hojas_muertas(nodo.b, out)
    
    def cleanup_dead(self):
        muertas = []
        self._hojas_muertas(self.root, muertas)
        
        self.matando = False

        for nodo in muertas:
            self.matando = True
            self._cerrar_nodo(nodo)
            
            
    def _recolectar_hojas(self, nodo, out):
        if isinstance(nodo, NodoVentana):
            out.append(nodo)
        elif isinstance(nodo, NodoSplit):
            self._recolectar_hojas(nodo.a, out)
            self._recolectar_hojas(nodo.b, out)
        
    def _reemplazar_nodo(self, actual, objetivo, nuevo):
        if isinstance(actual, NodoSplit):
            if actual.a == objetivo:
                actual.a = nuevo
                return True
            if actual.b == objetivo:
                actual.b = nuevo
                return True
            return(
                self._reemplazar_nodo(actual.a, objetivo, nuevo) or
                self._reemplazar_nodo(actual.b, objetivo, nuevo)
            )
        return False
        
    def _siguiente_ventana(self):
        hojas = []
        self._recolectar_hojas(self.root, hojas)
        
        if not hojas:
            return
            
        idx = hojas.index(self.activa)
        self.activa = hojas[(idx + 1)  % len(hojas)]
            
    def _anterior_ventana(self):
        hojas = []
        self._recolectar_hojas(self.root, hojas)
        
        if not hojas:
            return
            
        idx = hojas.index(self.activa)
        self.activa = hojas[(idx - 1)  % len(hojas)]
        
    def _usable_geometry(self):
        alto, ancho = self.stdscr.getmaxyx()
        return (0, 0, alto - 3, ancho)

    def _cerrar_nodo(self, nodo_a_cerrar): # Para cerrar una ventana automát. con gestor
        hojas = []
        self._recolectar_hojas(self.root, hojas)
        
        if len(hojas) == 1:
            raise SystemExit
        
        x, y, h, w = self._usable_geometry()
        old_layout = compute_layout(self.root, x, y, h, w)
        
        # Eliminación real
        self.root = self._eliminar_nodo(self.root, nodo_a_cerrar)
        self.activa = self._primera_hoja(self.root)        

        # Eliminar nodo simulado como si todavía estuviera
        new_layout = compute_layout(self.root, x, y, h, w)
        
        if self.animar:
            # Animación
            frames = self.animator.interpolate_destroy(old_layout, new_layout)
            for frame in frames:
                self.renderer.render(self.stdscr, frame)
                time.sleep(self.animator.delay)

        self.relayout()
        
         
    def _cerrar_activa(self): # Método para cerrar manualmente la ventana activa
        if self.root == self.activa:
            return  # no cerramos la última
        # Layout antes del cambio
        x, y, h, w = self._usable_geometry()
        old_layout = compute_layout(self.root, x, y, h, w)

        # Nodo que vamos a cerrar
        nodo_a_cerrar = self.activa

        # Eliminación real
        self.root = self._eliminar_nodo(self.root, nodo_a_cerrar)
        self.activa = self._primera_hoja(self.root)

        # Layout después del cambio
        new_layout = compute_layout(self.root, x, y, h, w)
        
        if self.animar:
            # Animación (solo marcos)
            frames = self.animator.interpolate_destroy(old_layout, new_layout)
            for frame in frames:
                self.renderer.render(self.stdscr, frame)
                time.sleep(self.animator.delay)
                
        # Estado final real (texto + cursores)
        self.relayout()
    
        
    def _eliminar_nodo(self, nodo, objetivo):
        if nodo is None:
            return None
        if nodo == objetivo:
            return None
            
        if isinstance(nodo, NodoSplit):
            if nodo.a == objetivo:
                return nodo.b
            if nodo.b == objetivo:
                return nodo.a
                
            nodo.a = self._eliminar_nodo(nodo.a, objetivo)
            nodo.b = self._eliminar_nodo(nodo.b, objetivo)
            
            if nodo.a is None:
                return nodo.b
            if nodo.b is None:
                return nodo.a
        return nodo
        
    def _primera_hoja(self, nodo):
        if isinstance(nodo, NodoVentana):
            return nodo # Si el nodo es tipo NodoVentana es porque no hay otra hoja más

        return self._primera_hoja(nodo.a)
        

    def relayout(self):
        if not self.root:
            return
        alto, ancho = self.stdscr.getmaxyx()
        usable_h = alto - 3
        self.root.layout(0, 0, usable_h, ancho)
        
    def draw(self):
        if self.root:
            self._draw_nodo(self.root)
        
    def resize(self):
        self.relayout()
    
    def _draw_nodo(self, nodo):
        if isinstance(nodo, NodoVentana):
            # Calcula índice de hojas
            hojas = []
            self._recolectar_hojas(self.root, hojas)
            index = hojas.index(nodo) + 1  # 1 a 9
            
            nodo.cuadro.draw(activa=(nodo == self.activa), index=index)
        elif isinstance(nodo, NodoSplit):
            self._draw_nodo(nodo.a)
            self._draw_nodo(nodo.b)
    



