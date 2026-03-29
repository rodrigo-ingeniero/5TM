class Nodo:
    def __init__(self, kind, children=None, window_id=None):
        self.kind = kind  # "leaf", "h", "v"
        self.children = children or []
        self.window_id = window_id
        self.index = None
        
    def es_hoja(self):
        if self.kind == "self":
            return True
        else:
            return False
        
    def es_contenedor(self):
        return self.kind in ("h", "v")
        
class NodoVentana(Nodo):
    def __init__(self, cuadro):
        self.cuadro = cuadro
        
    def es_hoja(self):
        return True

    def layout(self, y, x, h, w):
        if h <= 0 or w <= 0:
            return
        self.cuadro.move_resize(y, x, h, w)
        
    def draw(self, activa=False):
        self.cuadro.draw(activa)
        
    def is_dead(self):
        return self.cuadro.dead
        
class NodoSplit(Nodo):
    def __init__(self, orientacion, a, b, ratio=0.5):
        self.orientacion = orientacion  # 'v' o 'h'
        self.a = a
        self.b = b
        self.ratio = ratio  # porcentaje del espacio
        
    def layout(self, y, x, h, w):
        if h <= 1 or w <= 1:
            return
        
        if self.orientacion == 'v':
            
            w_a = int(w * self.ratio)
            w_a = max(1, w_a)
            w_b = max(1, w - w_a)

            self.a.layout(y, x, h, w_a)
            self.b.layout(y, x + w_a, h, w_b)

        else:  # horizontal
            h_a = int(h * self.ratio)
            h_a = max(1, h_a)
            h_b = max(1, h - h_a)

            self.a.layout(y, x, h_a, w)
            self.b.layout(y + h_a, x, h_b, w)
    

