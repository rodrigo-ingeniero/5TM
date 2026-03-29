import curses

class Renderer:
    def render(self, stdscr, layout):
        stdscr.erase()
        
        for r in layout:
            if r.w < 2 or r.h < 2:
                continue

            win = curses.newwin(r.h, r.w, r.y, r.x)
            win.box()
            win.noutrefresh()

        curses.doupdate()
        

            
    
    
            
