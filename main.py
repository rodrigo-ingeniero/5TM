import curses
from curses import wrapper
import time
import os
import signal
from gestor_ventanas import GestorVentanas
from estado_red import EstadoRed
from medidor_cpu import MedidorCPU
from sesion_terminal import SesionTerminal
    
def main(stdscr):
    # -------------- Configuración inicial --------------------------
    curses.noecho() # La terminal no imprime teclas pulsadas
    curses.curs_set(0) # No muestra el cursor de terminal
    curses.raw() # Capturar todo (para enviar Control + C a un programa)
    #stdscr.keypad(False) # Admite teclas especiales (flechas, enter, escape)
    stdscr.timeout(16) # La obtención de la entrada espera unos 16 ms (unos 60 Hz)
    
    signal.signal(signal.SIGINT, signal.SIG_IGN) # Evita salir del programa principal con Control + C
    
    curses.start_color() # Arranca el sistema de colores
    if curses.has_colors():
        if curses.COLORS >= 256:
            fondo = 17
        else:
            fondo = curses.COLOR_BLUE
        curses.init_pair(1, curses.COLOR_WHITE,fondo) # Color de la aplicación
        curses.init_pair(2, fondo, curses.COLOR_WHITE) # Opción resaltada
        curses.init_pair(3, curses.COLOR_CYAN, fondo) # Para el borde del cuadro con foco
        curses.init_pair(4, curses.COLOR_YELLOW, fondo) # Para el borde en Tab mode
        
    # Tamaño pantalla inicial
    tamano_pantalla = stdscr.getmaxyx()
    ancho_pantalla = tamano_pantalla[1]
    alto_pantalla = tamano_pantalla[0]
    
    # Datos/estados de la interfaz
    hora = time.strftime("%Y-%m-%d %H:%M")
    medidor_cpu = MedidorCPU(3) # Cada X segundos actualizar el uso de CPU
    uso_cpu = medidor_cpu.read()
    red = EstadoRed(include_ssid=True, refresh_interval=3.0) # Cada 3 seg actualizar ip
    red.start()
    indicadores_guardados = ""
    entrada = -1
    entrada_guardada = -1
    
    # Se dibuja la barra inferior
    barra_inferior = curses.newwin(3,ancho_pantalla,alto_pantalla-3,0)
    barra_inferior.bkgd(' ', curses.color_pair(1))
    
    # Añadimos el gestor de ventanas y creamos el primer cuadro
    gv = GestorVentanas(stdscr)
    gv.create_initial_window()
    gv.relayout()
    ventana_activa = gv.activa
    ventana_root = gv.root
    ventana_guardada = ventana_activa

    # Lógicas para el bucle
    sucio = True
    ejecutando = True
              
    def prueba_string(mensaje: str, ventana: win, posicion_x: int, posicion_y: int = 1, activo: bool = True):
        # Función para intentar dibujar una cadena, con justificación horizontal y vertical
        if activo:
            x = 0
            y = 0
            alto_ventana, ancho_ventana = ventana.getmaxyx()
            if posicion_x == 0: # Posición izquierda
                x = 1
            elif posicion_x == 1: # Posición centro
                x = int(ancho_ventana/2) - int(len(mensaje)/2)
            elif posicion_x == 2: # Posición derecha
                x = ancho_ventana - int(len(mensaje)) - 2
            else:
                x = 1
            # Intenta dibujar
            try:
                ventana.addstr(posicion_y,x,mensaje)
            except curses.error:
                pass
    
    def dibujar_barra_inf():
        barra_inferior.erase()
        barra_inferior.box()
        barra_inferior.bkgd(' ', curses.color_pair(1))
        
        #prueba_string(f"Tecla: {entrada_guardada}", barra_inferior, 0 , 0)
        #prueba_string(f"{ventana_activa}//{ventana_root}", barra_inferior, 1 , 0) # Debug
        #rowsYcols = ventana_activa.cuadro.terminal.get_inner_size()
        #prueba_string(f"{rowsYcols}", barra_inferior, 1 , 0)
        
        if uso_cpu != None:
            if uso_cpu == 100:
                prueba_string(f" CPU: 100%", barra_inferior, 0)
            else:
                prueba_string(f" CPU: {uso_cpu}%", barra_inferior, 0)
        else:
            prueba_string("¡No psutil!", barra_inferior, 0)
        if ip != None:
            prueba_string(ip, barra_inferior, 1)
        else:
            prueba_string("Sin Red", barra_inferior, 1)
        prueba_string(hora, barra_inferior, 2)
    
    while ejecutando:
        
        entrada = stdscr.getch()
        # ------------------ Window Manager ------------------
        # Si el WM consume la tecla
        if gv.matando:
            # Destruimos la ventana supuestamente activa para corregir la hoja
            entrada = 165
        if gv.handle_key(entrada):
            ventana_activa = gv.activa
            ventana_root = gv.root
            # Se pulsa retroceso dos veces para corregir una señal extra que entra
            ventana_guardada.cuadro.send_key(127)
            ventana_guardada.cuadro.send_key(127)
            
            ventana_guardada = ventana_activa
            sucio = True
        else:
            # ------------------ Reenviar input a ventana activa ------------------ 
            ventana_activa.cuadro.send_key(entrada)
            sucio = True

        # ------------------ Redimensionado ------------------
        nuevo_alto, nuevo_ancho = stdscr.getmaxyx()
        if (nuevo_ancho != ancho_pantalla) or (nuevo_alto != alto_pantalla):
            ancho_pantalla, alto_pantalla = nuevo_ancho, nuevo_alto
            gv.resize()
            try:
                barra_inferior.mvwin(alto_pantalla-3,0)
                dibujar_barra_inf()
            except curses.error:
                pass
            sucio = True

        # ------------------ Barra inferior con indicadores (actualizar)------------------
        uso_cpu = int(medidor_cpu.read())
        online, iface, ip, ssid = red.snapshot()
        hora = time.strftime("%Y-%m-%d %H:%M:%S")
        if entrada != -1:
            entrada_guardada = entrada
        try:
            xx_ven_activa = ventana_activa.cuadro.h, ventana_activa.cuadro.w
        except:
            xx_ven_activa = False
        
        indicadores = str(uso_cpu) + str(ip) + hora # Revisamos a la vez todos los indic.
        
        if indicadores_guardados != indicadores:
            sucio = True
            indicadores_guardados = indicadores
            
        # ---------------- Redibujo ------------------
        if sucio:
            gv.cleanup_dead()
            gv.draw()
            dibujar_barra_inf()
            barra_inferior.noutrefresh()
            curses.doupdate()

            sucio = False
            
# ----------------------------------------------------------------------------------    
# Captura de errores
if __name__ == "__main__":
    curses.wrapper(main)