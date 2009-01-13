#!/usr/bin/env python2.5

# Crunchbang Openbox Logout
#   - GTK/Cairo based logout box styled for Crunchbang
#
#    Andrew Williams <andy@tensixtyone.com>
#    adcomp <david.madbox@gmail.com>
#    iggykoopa <etrombly@yahoo.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import gtk, os
from PIL import Image, ImageFilter
import ConfigParser
import StringIO
import logging
import cairo
import gettext
import string

class OpenboxLogout():
    def __init__(self, config=None):
        
        self.validbuttons = ['cancel', 'logout', 'restart', 'shutdown', 'suspend', 'hibernate']
        
        self.load_config(config)
        
        gettext.install('cb-openbox-logout', 'po', unicode=1)
               
        self.window = gtk.Window()        
        self.window.set_title(_("logout"))
        
        self.window.connect("destroy", self.quit)
        self.window.connect("key-press-event", self.on_keypress)
        self.window.connect("window-state-event", self.on_window_state_change)
        
        if not self.window.is_composited():
            logging.debug("No compositing, enabling rendered effects")
            # Window isn't composited, enable rendered effects
            self.rendered_effects = True
        else:
            # Link in Cairo rendering events
            self.window.connect('expose-event', self.on_expose)
            self.window.connect('screen-changed', self.on_screen_changed)
            self.on_screen_changed(self.window)
            self.rendered_effects = False
        
        self.window.set_size_request(620,200)
        self.window.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
                   
        self.window.set_decorated(False)
        self.window.set_position(gtk.WIN_POS_CENTER)
        
        # Create the main panel box
        self.mainpanel = gtk.HBox()
        
        # Create the button box
        self.buttonpanel = gtk.HButtonBox()
        self.buttonpanel.set_spacing(10)
        
        # Pack in the button box into the panel box, with two padder boxes
        self.mainpanel.pack_start(gtk.VBox())
        self.mainpanel.pack_start(self.buttonpanel, False, False)
        self.mainpanel.pack_start(gtk.VBox())
                
        # Add the main panel to the window
        self.window.add(self.mainpanel)
         
        if self.button_list:
            list = map(lambda button: string.strip(button), self.button_list.split(","))
            for button in list:
                self.add_button(button, self.buttonpanel)
        else:
            for button in self.validbuttons:
                self.add_button(button, self.buttonpanel)            
                
        #self.add_button("cancel", self.buttonpanel)
        #self.add_button("logout", self.buttonpanel)
        #self.add_button("reboot", self.buttonpanel)
        #self.add_button("shutdown", self.buttonpanel)
               
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
                wh = (pb.get_width(),pb.get_height())
                pilimg = Image.fromstring("RGB", wh, pb.get_pixels())

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
        self.window.resize(gtk.gdk.screen_width(), gtk.gdk.screen_height())
        self.window.realize()
        if pixmap:
            self.window.window.set_back_pixmap(pixmap, False)
        self.window.move(0,0)
                  

    def load_config(self, config):
    
        if config == None:
            config = '/etc/cb-openbox-logout.conf'
            
        self.parser = ConfigParser.SafeConfigParser()
        self.parser.read(config)
        
        self.blur_background = self.parser.getboolean("looks", "blur")
        self.opacity = self.parser.getint("looks", "opacity")
        self.button_theme = self.parser.get("looks", "buttontheme")
        self.button_list = self.parser.get("looks", "buttonlist")
        
        # Validate configuration
        if not os.path.exists('img/%s/' % self.button_theme):
            logging.warning("Button theme %s not found, reverting to default" % self.button_theme)
            self.button_theme = 'default'
        
        try:  
            self.bgcolor = gtk.gdk.Color(self.parser.get("looks", "bgcolor"))
        except ValueError:
            logging.warning("Color %s is not a valid color, defaulting to black" % self.parser.get("looks", "bgcolor"))
            self.bgcolor = gtk.gdk.Color("black")
            
        if self.button_list:
            
            if self.button_list == "default":
                self.button_list = string.join(self.validbuttons,",")
            list = map(lambda button: string.strip(button), self.button_list.split(","))
            logging.debug("Button list: %s" % list)
        
            for button in list:
                if not button in self.validbuttons:
                    logging.warning("Button %s is not a valid button name, resetting to defaults" % button)
                    self.button_list = None
                    break
               
                
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
        cr.set_source_rgba(self.bgcolor.red, self.bgcolor.green, self.bgcolor.blue, float(self.opacity)/100)
       
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

    def add_button(self, name, widget):
    
        box = gtk.VBox()
   
        image = gtk.Image()
        image.set_from_file("img/%s/%s.png" % (self.button_theme, name))
        image.show()
        
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("black"))
        button.set_focus_on_click(False)
        button.set_border_width(0)
        button.set_property('can-focus', False) 
        button.add(image)
        button.show()
        box.pack_start(button, False, False)
        button.connect("clicked", self.click_button, name)
        
        label = gtk.Label(_(name))
        label.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse("white"))
        box.pack_end(label, False, False)
        
        widget.pack_start(box, False, False)

    def click_button(self, widget, data=None):
        if (data=='cancel'):
            self.quit()
        elif (data=='logout'):
            os.system('openbox --exit')
        elif (data=='restart'):
            os.system('gdm-control --reboot && openbox --exit')
        elif (data=='shutdown'):
            os.system('gdm-control --shutdown && openbox --exit')
        elif (data=='suspend'):
            os.system('dbus-send --session --dest=org.gnome.PowerManager --type=method_call --reply-timeout=2000 /org/gnome/PowerManager org.gnome.PowerManager.Suspend')
        elif (data=='hibernate'):
            os.system('dbus-send --session --dest=org.gnome.PowerManager --type=method_call --reply-timeout=2000 /org/gnome/PowerManager org.gnome.PowerManager.Hibernate')         

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
