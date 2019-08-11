#    This Addon for Blender implements realtime OSC controls in the viewport
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#    Copyright (C) 2015  JPfeP <http://www.jpfep.net/>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ***** END GPL LICENCE BLOCK *****

# TODO:
#
# attach the timer to the context window or not ?
# pbm not set to None du modal timer when opening a new blend file
# Bool are not part of OSC 1.0 (only later as extension)
# Deal with tupple (x,y,z) or (r,g,b) usr "type(key).__name__" for Vector, Euler, etc... 
# Monitoring in console report error "Improper..." due to Monitoring refresh hack overhead 


bl_info = {
    "name": "AddOSC",
    "author": "JPfeP, Kevan Cress",
    "version": (0, 16),
    "blender": (2, 80, 6),
    "location": "",
    "description": "Realtime control of Blender using OSC protocol",
    "warning": "Please read the disclaimer about network security on my site.",
    "wiki_url": "http://www.jpfep.net/pages/addosc/",
    "tracker_url": "",
    "category": "System"}

import bpy

import sys
from select import select
import socket
import errno
from math import radians
from bpy.props import *

import os
script_file = os.path.realpath(__file__)
directory = os.path.dirname(script_file)
if directory not in sys.path:
   sys.path.append(directory)

from pythonosc import osc_message_builder
from pythonosc import udp_client
from pythonosc import osc_bundle
from pythonosc import osc_message
from pythonosc import osc_packet
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import socketserver
from bpy.app.handlers import persistent
from bpy.utils import register_class
from bpy.utils import unregister_class

from . import auto_load
auto_load.init()




#Restore saved settings
@persistent
def addosc_handler(scene):
    for text in bpy.data.texts:
        if text.name == '.addosc_settings':
            try:
                bpy.context.window_manager.addosc_monitor = int(text.lines[0].body)
            except:
                pass
            try:
                bpy.context.window_manager.addosc_port_in  = int(text.lines[1].body)
            except:
                pass
            try:
                bpy.context.window_manager.addosc_port_out = int(text.lines[2].body)
            except:
                pass
            try:
                bpy.context.window_manager.addosc_rate = int(text.lines[3].body) 
            except:
                bpy.context.window_manager.addosc_rate = 10
            if text.lines[4].body != '':
                bpy.context.window_manager.addosc_udp_in = text.lines[4].body 
            if text.lines[5].body != '':
                bpy.context.window_manager.addosc_udp_out = text.lines[5].body 
            try:
                bpy.context.window_manager.addosc_autorun = int(text.lines[6].body) 
            except:
                pass

            #if error_device == True:
            #    bpy.context.window_manager.addosc_autorun = False

            if bpy.context.window_manager.addosc_autorun == True:
                bpy.ops.addosc.startudp()  


def register():
    auto_load.register()
    bpy.app.handlers.load_post.append(addosc_handler)
        
def unregister():
    auto_load.unregister()
if __name__ == "__main__": 
    register()
 
 

