#!/usr/bin/env python2.5

# Crunchbang Openbox Logout
#   - GTK/Cairo based logout box styled for Crunchbang
#
#    Andrew Williams <andy@tensixtyone.com>
#
#    Originally based on code by:
#       adcomp <david.madbox@gmail.com>
#       iggykoopa <etrombly@yahoo.com>
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
import dbus

class OpenboxLogout():
    def __init__(self, config=None):
    
        # Start logger and gettext/i18n
        self.logger = logging.getLogger('OpenboxLogout')
        gettext.install('openboxlogout', '%s/locale' % self.determine_path(), unicode=1)      
                          
        # Start dbus interface
        bus = dbus.SystemBus()
        dbus_hal = bus.get_object("org.freedesktop.Hal", "/org/freedesktop/Hal/devices/computer")
        self.dbus_powermanagement = dbus.Interface(dbus_hal, "org.freedesktop.Hal.Device.SystemPowerManagement")
        
        # Load configuration file
        self.load_config(config)
               
        # Start pyGTK setup       
        self.window = gtk.Window()        
        self.window.set_title(_("Openbox Logout"))
        
        self.window.connect("destroy", self.quit)
        self.window.connect("key-press-event", self.on_keypress)
        self.window.connect("window-state-event", self.on_window_state_change)
        
        if not self.window.is_composited():
            self.logger.debug("No compositing, enabling rendered effects")
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
         
        for button in self.button_list:
            self.add_button(button, self.buttonpanel)          
                               
        if self.rendered_effects == True:    
            self.logger.debug("Stepping though render path")
            w = gtk.gdk.get_default_root_window()
            sz = w.get_size()
            pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,sz[0],sz[1])
            pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,sz[0],sz[1])

            self.logger.debug("Rendering Blur")
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
        
    def determine_path(self):
        """Borrowed from wxglade.py"""
        try:
            root = __file__
            if os.path.islink (root):
                root = os.path.realpath (root)
            return os.path.dirname (os.path.abspath (root))
        except:
            self.logger.error(_("Unable to determin the module path, exiting..."))
            sys.exit()
             

    def load_config(self, config):
        """ Load the configuration file and parse entries, when encountering a issue
            change safe defaults """
    
        if config == None:
            config = '/etc/openbox-logout.conf'
            
        if not os.path.exists(config):
            self.logger.error(_("Unable to find config file %s") % config)
            exit()
            
        self.parser = ConfigParser.SafeConfigParser()
        self.parser.read(config)
        
        # Read config file values
        try:
            self.opacity = self.parser.getint("looks", "opacity")
        except:
            self.opacity = 50
        
        # Validate theme configuration 
        self.img_path = "%s/themes" % self.determine_path()
        
        try:
            self.button_theme = self.parser.get("looks", "buttontheme")
        except:
            self.button_theme = "default"
        
        if os.path.exists("%s/.themes/%s/oblogout" % (os.environ['HOME'], self.button_theme)):
            # Found a valid theme folder in the userdir, use that
            self.img_path = "%s/.themes/%s/oblogout" % (os.environ['HOME'], self.button_theme)
            self.logger.info("Using user theme at %s" % self.img_path)
        else:
            if not os.path.exists('%s/%s/' % (self.img_path, self.button_theme)):
                self.logger.warning("Button theme %s not found, reverting to default" % self.button_theme)
                self.button_theme = 'default'
        
        # Set background color
        try:  
            self.bgcolor = gtk.gdk.Color(self.parser.get("looks", "bgcolor"))
        except ValueError:
            self.logger.warning(_("Color %s is not a valid color, defaulting to black") % self.parser.get("looks", "bgcolor"))
            self.bgcolor = gtk.gdk.Color("black")

        # Load and parse button list
        validbuttons = ['cancel', 'logout', 'restart', 'shutdown', 'suspend', 'hibernate', 'safesuspend', 'lock', 'switch']  
        buttonname = [_('cancel'), _('logout'), _('restart'), _('shutdown'), _('suspend'), _('hibernate'), _('safesuspend'), _('lock'), _('switch')] 
        
        try:
            blist = self.parser.get("looks", "buttons")
        except:
            blist = ""
            
        if not blist:
            list = validbuttons
        elif blist == "default":
            list = validbuttons
        else:
            list = map(lambda button: string.strip(button), blist.split(","))
                    
        # Validate the button list
        for button in list:
            if not button in validbuttons:
                self.logger.warning(_("Button %s is not a valid button name, removing") % button)
                list.remove(button)
            else:
                if button == 'suspend':
                    if not self.dbus_powermanagement.CanSuspend:
                        self.logger.warning(_("Can't Suspend, disabling button"))
                        list.remove(button)
                elif button == 'hibernate':
                    if not self.dbus_powermanagement.CanHibernate:
                        self.logger.warning(_("Can't Hibernate, disabling button"))
                        list.remove(button)  
                elif button == 'safesuspend':
                     if not self.dbus_powermanagement.CanHibernate or not self.dbus_powermanagement.CanSuspend:
                        self.logger.warning(_("Can't Safe Suspend, disabling button"))
                        list.remove(button)
                        
        if len(list) == 0:
            self.logger.warning(_("No valid buttons found, resetting to defaults"))
            self.button_list = validbuttons
        else:
            self.logger.debug("Validated Button List: %s" % list)
            self.button_list = list
                                     
                
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
            self.logger.debug("Screen does not support alpha channels!")
            colormap = screen.get_rgb_colormap()
            self.supports_alpha = False
        else:
            self.logger.debug("Screen supports alpha channels!")
            self.supports_alpha = True
    
        # Now we have a colormap appropriate for the screen, use it
        widget.set_colormap(colormap)

    def on_window_state_change(self, widget, event, *args):
        if event.new_window_state & gtk.gdk.WINDOW_STATE_FULLSCREEN:
            self.window_in_fullscreen = True
        else:
            self.window_in_fullscreen = False

    def add_button(self, name, widget):
        """ Add a button to the panel """
    
        box = gtk.VBox()
   
        image = gtk.Image()
        image.set_from_file("%s/%s/%s.png" % (self.img_path, self.button_theme, name))
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
        if (data == 'cancel'):
            self.quit()
        elif (data == 'logout'):
            os.system('openbox --exit')
        elif (data == 'restart'):
            self.dbus_powermanagement.Reboot()
            #os.system('gdm-control --reboot && openbox --exit')
        elif (data == 'shutdown'):
            self.dbus_powermanagement.Shutdown()
            #os.system('gdm-control --shutdown && openbox --exit')
        elif (data == 'suspend'):
            self.dbus_powermanagement.Suspend(0)
            #os.system('dbus-send --system --print-reply --dest=org.freedesktop.Hal /org/freedesktop/Hal/devices/computer org.freedesktop.Hal.Device.SystemPowerManagement.Suspend int32:0')
            self.quit()
        elif (data == 'hibernate'):
            self.dbus_powermanagement.Hiberate()
            #os.system('dbus-send --system --print-reply --dest=org.freedesktop.Hal /org/freedesktop/Hal/devices/computer org.freedesktop.Hal.Device.SystemPowerManagement.Hibernate')         
            self.quit()
        elif (data == 'safesuspend'):
            self.dbus_powermanagement.SuspendHybrid(0)
            #os.system('dbus-send --system --print-reply --dest=org.freedesktop.Hal /org/freedesktop/Hal/devices/computer org.freedesktop.Hal.Device.SystemPowerManagement.SuspendHybrid int32:0')         
            self.quit()
        elif (data == 'lock'):
            os.system('gnome-screensaver-command -l')
            self.quit()
        elif (data == 'switch'):
            os.system('gdm-control --switch-user')
            self.quit()
            
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
     
     if os.path.exists('openbox-logout.conf'):
        config = 'openbox-logout.conf'
     else:
        config = None
        
     app = OpenboxLogout(config)
     app.run() 
