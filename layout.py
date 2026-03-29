from dataclasses import dataclass
from nodo import NodoVentana, NodoSplit

@dataclass
class Rect:
    window_id: str
    x: int
    y: int
    w: int
    h: int
    
def compute_layout(nodo, x, y, h, w) -> list[Rect]:
    rects = []

    if isinstance(nodo, NodoVentana):
        rects.append(Rect(
            window_id=id(nodo.cuadro),   # o como identifiques la ventana
            x=x,
            y=y,
            w=w,
            h=h
        ))

    elif isinstance(nodo, NodoSplit):
        if nodo.orientacion == 'v':
            w1 = w // 2
            w2 = w - w1
            rects += compute_layout(nodo.a, x, y, h, w1)
            rects += compute_layout(nodo.b, x + w1, y, h, w2)

        else:  # 'h'
            h1 = h // 2
            h2 = h - h1
            rects += compute_layout(nodo.a, x, y, h1, w)
            rects += compute_layout(nodo.b, x, y + h1, h2, w)

    return rects
    
def rect_changed(r0: Rect | None, r1: Rect | None) -> bool:
    if r0 is None or r1 is None:
        return True
    return (r0.x, r0.y, r0.w, r0.h) != (r1.x, r1.y, r1.w, r1.h)

        
class LayoutAnimator:
    def __init__(self, steps=100, delay=0.002):
        self.steps = steps
        self.delay = delay    

    def interpolate_destroy(self, old, new):
        """
        Genera frames de animación entre old y new layouts.
        - old: lista de Rect (layout antes)
        - new: lista de Rect (layout después)
        """
        frames = []

        old_map = {r.window_id: r for r in old}
        new_map = {r.window_id: r for r in new} 
        ids = old_map.keys() | new_map.keys()

        for i in range(self.steps+1):
            t = i / self.steps
            t = 1 - (1 - t) ** 4
            frame = []

            for wid in ids:
                r0 = old_map.get(wid)
                r1 = new_map.get(wid)
                # Animación de cerrar ventana
                if r0 and r1:
                    # interpolación normal
                    frame.append(Rect(
                        wid,
                        int(r0.x + (r1.x - r0.x) * t),
                        int(r0.y + (r1.y - r0.y) * t),
                        max(1, int(r0.w + (r1.w - r0.w) * t)),
                        max(1, int(r0.h + (r1.h - r0.h) * t)),
                    ))                     
            frames.append(frame)

        return frames
        
    def ease_out_back(self, t, s=1.5):
        t -= 1
        return 1 + t * t * ((s + 1) * t + s)
        
    def interpolate_create(self, orientacion, old, new):
        """
        Genera frames de animación entre old y new layouts.
        - old: lista de Rect (layout antes)
        - new: lista de Rect (layout después)
        """
        frames = []

        old_map = {r.window_id: r for r in old}
        new_map = {r.window_id: r for r in new}
        
        no_entrar=False
        
        # Solo animamos las 2 ventanas implicadas (la nueva y la que se parte)
        animated_ids = set() 
        for wid in old_map.keys() | new_map.keys():
            r0 = old_map.get(wid)
            r1 = new_map.get(wid)

            if r0 is None or r1 is None:
                animated_ids.add(wid)
            elif (r0.x, r0.y, r0.w, r0.h) != (r1.x, r1.y, r1.w, r1.h):
                animated_ids.add(wid)
                
        for wid in animated_ids:
            r0 = old_map.get(wid)
            r1 = new_map.get(wid)
            if r0 and r1:
                # este es el cuadro original que se está partiendo
                split_origin = r0
                break
            
        for i in range(self.steps+1):
            raw = i / self.steps
            t = self.ease_out_back(raw)
            frame = []

            for wid in animated_ids:
                r0 = old_map.get(wid)
                r1 = new_map.get(wid)
                # Animación partir una ventana en dos
                if orientacion == "v": # Animación partir vertical
                    if r0 and r1:
                        # Ventana original encoge hacia la izquierda
                        frame.append(Rect(
                            wid,
                            int(r0.x + (r1.x - r0.x) * t),
                            int(r0.y + (r1.y - r0.y) * t),
                            max(1, int(r0.w + (r1.w - r0.w) * t)),
                            max(1, int(r0.h + (r1.h - r0.h) * t)),
                        ))
                    elif r1 and not r0 and split_origin:
                        o = split_origin # Ventana nueva crece hacia la izquierda
                        calculo = int(r1.w*t) + int((o.x + o.w) + (r1.x - (o.x + o.w)) * t)
                        if calculo < o.w:
                            correccion = int(o.w - calculo)
                        else:
                            correccion = 0
                        frame.append(Rect(
                            wid,
                            int((o.x + o.w) + (r1.x - (o.x + o.w)) * t),
                            int(o.y + (r1.y - o.y) * t),
                            max(1, int(r1.w*t))+correccion,
                            max(1, int(o.h + (r1.h - o.h) * t)),
                        ))
                else: # Animación partir horizontal
                    if r0 and r1:
                        # Ventana original encoge hacia arriba
                        frame.append(Rect(
                            wid,
                            int(r0.x + (r1.x - r0.x) * t),
                            int(r0.y + (r1.y - r0.y) * t),
                            max(1, int(r0.w + (r1.w - r0.w) * t)),
                            max(1, int(r0.h + (r1.h - r0.h) * t)),
                        ))
                    elif r1 and not r0 and split_origin:
                        o = split_origin # Ventana nueva crece hacia arriba
                        calculo = int(r1.h*t) + int((o.y + o.h) + (r1.y - (o.y + o.h)) * t)
                        if calculo < o.h:
                            correccion = o.h - calculo
                        else:
                            correccion = 0
                        frame.append(Rect(
                            wid,
                            int(o.x + (r1.x - o.x) * t),
                            int((o.y + o.h) + (r1.y - (o.y + o.h)) * t),
                            max(1, int(o.w + (r1.w - o.w) * t)),
                            int(r1.h*t)+correccion,
                        ))
                                             
            frames.append(frame)

        return frames