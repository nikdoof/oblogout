#!/usr/bin/env python2.5

import gtk, os
from PIL import Image, ImageFilter
import ConfigParser
import StringIO
import logging
import cairo

class OpenboxLogout():
    def __init__(self, config=None):
        
        self.load_config(config)
               
        self.window = gtk.Window()        
        self.window.set_title("Log Out ..")
        
        self.window.connect("destroy", self.quit)
        self.window.connect("key-press-event", self.on_keypress)
        self.window.connect("window-state-event", self.on_window_state_change)
        
        if self.rendered_effects == False:     
            if not self.window.is_composited():
                logging.debug("No compositing, enabling rendered effects")
                # Window isn't composited, enable rendered effects
                self.rendered_effects = True
            else:
                # Link in Cairo rendering events
                self.window.connect('expose-event', self.on_expose)
                self.window.connect('screen-changed', self.on_screen_changed)
                self.on_screen_changed(self.window)
        
        self.window.set_size_request(620,200)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
                   
        self.window.set_decorated(False)
        self.window.set_position(gtk.WIN_POS_CENTER)
        
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
        
        if self.rendered_effects == True:
        
            logging.debug("Stepping though render path")
            w = gtk.gdk.get_default_root_window()
            sz = w.get_size()
            pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
            pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])

            logging.debug("Blur Enabled: %s" % self.blur_background)
            if self.blur_background == True:
                logging.debug("Rendering Blur")
                # Convert Pixbuf to PIL Image
                width,height = pb.get_width(),pb.get_height()
                pilimg = Image.fromstring("RGB",(width,height),pb.get_pixels() )

                # Blur the image
                pilimg = pilimg.filter(ImageFilter.BLUR)
    
                # "Convert" the PIL to Pixbuf via PixbufLoader
                buf = StringIO.StringIO()
                pilimg.save(buf, "ppm")
                del pilimg
                loader = gtk.gdk.PixbufLoader("pnm")
                loader.write(buf.getvalue())
                pixbuf = loader.get_pixbuf()

                # Cleanup IO
                buf.close()
                loader.close()
            else:
                pixbuf = pb
                del pb

            pixmap, mask = pixbuf.render_pixmap_and_mask()
            # width, height = pixmap.get_size()
        else:
            pixmap = None
    
        self.window.set_app_paintable(True)
        self.window.resize(screen_x, screen_y)
        self.window.realize()
        if pixmap:
            self.window.window.set_back_pixmap(pixmap, False)
        self.window.move(0,0)
                  

    def load_config(self, config):
    
        if config == None:
            config = '/etc/cb-openbox-logout.conf'
            
        parser = ConfigParser.SafeConfigParser()
        parser.read(config)
        
        self.blur_background = parser.getboolean("looks", "blur")
        self.opacity = parser.getint("looks", "opacity")
        
        print self.blur_background
        
        if self.blur_background:
            self.rendered_effects = True
        else:
            self.rendered_effects = False

    def on_expose(self, widget, event):
       
        cr = widget.window.cairo_create()
    
        if self.supports_alpha == True:
            cr.set_source_rgba(1.0, 1.0, 1.0, 0.0) # Transparent
        else:
            cr.set_source_rgb(1.0, 1.0, 1.0) # Opaque white
    
        # Draw the background
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        (width, height) = widget.get_size()
        cr.set_source_rgba(0, 0, 0, .5)
       
        cr.rectangle(0, 0, width, height)
        cr.fill()
        cr.stroke()
        return False
        
    def on_screen_changed(self, widget, old_screen=None):
       
        # To check if the display supports alpha channels, get the colormap
        screen = widget.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap == None:
            logging.debug('Screen does not support alpha channels!')
            colormap = screen.get_rgb_colormap()
            self.supports_alpha = False
        else:
            logging.debug('Screen supports alpha channels!')
            self.supports_alpha = True
    
        # Now we have a colormap appropriate for the screen, use it
        widget.set_colormap(colormap)

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
            self.quit()
        elif (data=='logout'):
            os.system('openbox --exit')
        elif (data=='reboot'):
            os.system('gdm-control --reboot && openbox --exit')
        elif (data=='shutdown'):
            os.system('gdm-control --shutdown && openbox --exit')
            

    def on_keypress(self, widget=None, event=None, data=None):
        if event.keyval == gtk.keysyms.Escape:
            self.quit() 
    
    def quit(self, widget=None, data=None):
        gtk.main_quit()

    def run(self):
        self.window.show_all()
        gtk.main()

if __name__ == "__main__":

     logging.basicConfig(level=logging.DEBUG)
     app = OpenboxLogout('openbox-logout.conf')
     app.run() 
