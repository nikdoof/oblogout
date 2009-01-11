#!/usr/bin/env python2.5

import gtk, os
from PIL import Image, ImageFilter

class MyApp():
    def __init__(self):
        
        self.window = gtk.Window()        
        self.window.set_title("Log Out ..")
        self.window.connect("destroy", self.doquit)
        self.window.connect("key-press-event", self.onkeypress)
        self.window.set_size_request(620,200)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        self.window.set_decorated(gtk.FALSE)
        self.window.set_position(gtk.WIN_POS_CENTER)

        self.window.connect("window-state-event", self.on_window_state_change)
        
        self.mainpanel = gtk.Fixed()
        self.window.add(self.mainpanel)
        
        screen_x , screen_y = gtk.gdk.screen_width(), gtk.gdk.screen_height()
        
        x = ( screen_x / 2 ) - 300
        y = ( screen_y / 2 ) - 150
        
        self.add_bouton("esc",x+30,y+30, self.mainpanel)
        self.add_bouton("logout",x+170,y+30, self.mainpanel)
        self.add_bouton("reboot",x+310,y+30, self.mainpanel)
        self.add_bouton("shutdown",x+450,y+30, self.mainpanel)
        
        self.label_info = gtk.Label('Cancel')
        self.label_info.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.mainpanel.put(self.label_info, x+80, y+170)
        
        self.label_info = gtk.Label('Logout')
        self.label_info.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.mainpanel.put(self.label_info, x+220, y+170)
        
        self.label_info = gtk.Label('Reboot')
        self.label_info.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.mainpanel.put(self.label_info, x+360, y+170)
        
        self.label_info = gtk.Label('Shutdown')
        self.label_info.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        self.mainpanel.put(self.label_info, x+490, y+170)
        
        w = gtk.gdk.get_default_root_window()
        sz = w.get_size()
        pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
        pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])

        pixbuf = pb
        pixmap, mask = pixbuf.render_pixmap_and_mask()
        # width, height = pixmap.get_size()
        self.window.set_app_paintable(True)
        self.window.resize(screen_x, screen_y)
        self.window.realize()
        self.window.window.set_back_pixmap(pixmap, False)
        self.window.move(0,0)
        del pixbuf
        del pixmap                   

    def on_window_state_change(self, widget, event, *args):
        if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.window_in_fullscreen = True
        else:
            self.window_in_fullscreen = False

    def add_bouton(self, name, x, y, page):
        image = gtk.Image()
        image.set_from_file("img/" + name + ".png")
        image.show()
        # un bouton pour contenir le widget image
        bouton = gtk.Button()
        bouton.set_relief(gtk.RELIEF_NONE)
        bouton.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        bouton.set_focus_on_click(False)
        bouton.set_border_width(0)
        bouton.set_property('can-focus', False) 
        bouton.add(image)
        #bouton.set_style(self.style)
        bouton.show()
        page.put(bouton, x,y)
        bouton.connect("clicked", self.clic_bouton, name)

    # Cette fonction est invoquee quand on clique sur un bouton.
    def clic_bouton(self, widget, data=None):
        if (data=='esc'):
            self.doquit()
        elif (data=='logout'):
            os.system('openbox --exit')
        elif (data=='reboot'):
            os.system('gdm-control --reboot && openbox --exit')
        elif (data=='shutdown'):
            os.system('gdm-control --shutdown && openbox --exit')
            

    def onkeypress(self, widget=None, event=None, data=None):
        if event.keyval == gtk.keysyms.Escape:
            self.doquit() 
    
    def doquit(self, widget=None, data=None):
        gtk.main_quit()

    def run(self):
        self.window.show_all()
        gtk.main()

app = MyApp()
app.run() 
