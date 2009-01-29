#!/usr/bin/python

import os, sys, glob, fnmatch

## Added 10 Jan 2008
from distutils.core import setup, Extension
import distutils.command.install_data
from distutils.core import setup
from DistUtilsExtra.command import *

setup(name = "oblogout",
    version = "0.2",
    description = "Openbox Logout",
    author = "Andrew Williams",
    author_email = "andy@tensixtyone.com",
    url = "http://launchpad.net/oblogout/",
    
    packages = ['oblogout'],
    scripts = ["data/oblogout"],
    data_files = [('share/themes/foom/oblogout', glob.glob('data/themes/foom/oblogout/*')),
                 ('share/themes/oxygen/oblogout', glob.glob('data/themes/oxygen/oblogout/*')),
                 ('/etc/', glob.glob('data/openbox-logout.conf'))],
    
    cmdclass = { 'build' : build_extra.build_extra,
                 'build_i18n' :  build_i18n.build_i18n },


    long_description = """Really long text here."""     
) 
