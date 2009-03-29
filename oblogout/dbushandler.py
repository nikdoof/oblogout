#!/usr/bin/env python

# Crunchbang Openbox Logout
#   - GTK/Cairo based logout box styled for Crunchbang
#
#    Andrew Williams <andy@tensixtyone.com>
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

import logging
import os
import dbus

class DbusController (object):

    def __init__(self):
        self.logger = logging.getLogger('oblogout.obdbus')

    def __check_perms(self, id):   
        """ Check if we have permissions for a action """

        self.logger.debug('Checking permissions for %s' % id)

        kit = dbus.SystemBus().get_object('org.freedesktop.PolicyKit','/')
        if(kit == None):
            print("Error: Could not get PolicyKit D-Bus Interface\n")
            return False

        try:
            res = kit.IsProcessAuthorized(id, dbus.UInt32(os.getpid()), False)
        except:
            return False

        if res:
            self.logging.debug("Authorised to use %s" % id)
            return True

    def __auth_perms(self, id):   
        """ Check if we have permissions for a action, if not, try to obtain them via PolicyKit """
     
        if self.__check_perms(id):
            return True
        else:
            
            kit = dbus.SessionBus().get_object('org.freedesktop.PolicyKit.AuthenticationAgent','/')
            if(kit == None):
                print("Error: Could not get PolicyKit D-Bus Interface\n")
                return False
 
            return kit.ObtainAuthorization(id, dbus.UInt32(0), dbus.UInt32(os.getpid()))

    def __get_sessions(self):
        """ Using DBus and ConsoleKit, get the number of sessions. This is used by PolicyKit to dictate the 
            multiple sessions permissions for the various reboot/shutdown commands """

        # Check the number of active sessions
        manager_obj = dbus.SystemBus().get_object ('org.freedesktop.ConsoleKit', '/org/freedesktop/ConsoleKit/Manager')
        manager = dbus.Interface (manager_obj, 'org.freedesktop.ConsoleKit.Manager')

        cnt = 0
        seats = manager.GetSeats ()
        for sid in seats:
            seat_obj = dbus.SystemBus().get_object ('org.freedesktop.ConsoleKit', sid)
            seat = dbus.Interface (seat_obj, 'org.freedesktop.ConsoleKit.Seat')
            cnt += len(seat.GetSessions())
            #print len(seat.GetSessions())

        return cnt


    def check_ability(self, action):
        """Check if HAL can complete action type requests, for example, suspend, hiberate, and safesuspend"""

        dbus_hal = dbus.SystemBus().get_object("org.freedesktop.Hal", "/org/freedesktop/Hal/devices/computer")
        pm = dbus.Interface(dbus_hal, "org.freedesktop.Hal.Device.SystemPowerManagement")

        if action == 'suspend':
            return pm.CanSuspend
        elif action == 'hibernate':
            return pm.CanHibernate
        elif action == 'safesuspend':
             if not pm.CanHibernate or not pm.CanSuspend:
                return False

        return True

    def restart(self):
        """Restart the system via HAL, if we do not have permissions to do so obtain them via PolicyKit"""

        if self.__get_sessions() > 1:
            if self.__auth_perms("org.freedesktop.hal.power-management.reboot-multiple-sessions"):
                dbus_hal = dbus.SystemBus().get_object("org.freedesktop.Hal", "/org/freedesktop/Hal/devices/computer")
                pm = dbus.Interface(dbus_hal, "org.freedesktop.Hal.Device.SystemPowerManagement")
                return pm.Reboot()
            else:
                return False

    def shutdown(self):
        """Shutdown the system via HAL, if we do not have permissions to do so obtain them via PolicyKit"""

        if self.__get_sessions() > 1:
            if self.__auth_perms("org.freedesktop.hal.power-management.shutdown-multiple-sessions"):
                dbus_hal = dbus.SystemBus().get_object("org.freedesktop.Hal", "/org/freedesktop/Hal/devices/computer")
                pm = dbus.Interface(dbus_hal, "org.freedesktop.Hal.Device.SystemPowerManagement")

                return pm.Shutdown()
            else:
                return False

        print 

    def suspend(self):
        pass

    def hibernate(self):
        pass

    def safesuspend(self):
        pass


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    t = DbusController()
    print t.restart()



