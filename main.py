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

from .message_parser import SceneSettingItem
##############################
### UI And Basic Operators ###
##############################

_report= ["",""] #This for reporting OS network errors 

# This Sets Object Values from OSC messages
def OSC_callback(*args):
    fail = True   
    bpy.context.window_manager.addosc_lastaddr = args[0]
    content=""
    for i in args[1:]:
        content += str(i)+" "
    bpy.context.window_manager.addosc_lastpayload = content
    
    # for simple properties
    if 'OSC_keys' in bpy.context.scene:
        for item in bpy.context.scene.OSC_keys:
            ob = item.data_path
            idx = 1 + item.idx
            
            if item.address == args[0]:
                #For ID custom properties (with brackets)
                if item.id[0:2] == '["' and item.id[-2:] == '"]':
                    try:
                        ob[item.id[2:-2]] = args[idx]
                        fail = False
                
                    except:
                        if bpy.context.window_manager.addosc_monitor == True:
                            print ("Improper content received: "+content+"for OSC route: "+args[0]+" and key: "+item.id)
                            
                #For normal properties
                #with index in brackets -: i_num
                elif item.id[-1] == ']':
                    d_p = item.id[:-3]
                    i_num = int(item.id[-2])
                    try:
                        getattr(ob,d_p)[i_num] = args[idx]
                        fail = False
                    except:
                        if bpy.context.window_manager.addosc_monitor == True: 
                            print ("Improper content received: "+content+"for OSC route: "+args[0]+" and key: "+item.id) 
                #without index in brackets
                else:
                    try:
                        setattr(ob,item.id,args[idx])
                        fail = False
                    except:
                        if bpy.context.window_manager.addosc_monitor == True: 
                            print ("Improper content received: "+content+"for OSC route: "+args[0]+" and key: "+item.id)
    
    # for parsed properties
    if 'OSC_Parsers' in bpy.context.scene:
        osc_address = args[0]
        osc_message = args[1]
        for parser in bpy.context.scene.OSC_Parsers:
            if osc_address == parser.messageAddress:
                stringlist = osc_message.split(parser.messageType)
                print(osc_address)
                print(str(stringlist[0]))


                                            
    if bpy.context.window_manager.addosc_monitor == True and fail == True: 
        print("Rejected OSC message, route: "+args[0]+" , content: "+content)

#For saving/restoring settings in the blendfile        
def upd_settings_sub(n):
    text_settings = None
    for text in bpy.data.texts:
        if text.name == '.addosc_settings':
            text_settings = text
    if text_settings == None:
        bpy.ops.text.new()
        text_settings = bpy.data.texts[-1]
        text_settings.name = '.addosc_settings'   
        text_settings.write("\n\n\n\n\n\n")
    if n==0:
        text_settings.lines[0].body = str(int(bpy.context.window_manager.addosc_monitor))
    elif n==1:
        text_settings.lines[1].body = str(bpy.context.window_manager.addosc_port_in)
    elif n==2:
        text_settings.lines[2].body = str(bpy.context.window_manager.addosc_port_out)
    elif n==3:
        text_settings.lines[3].body = str(bpy.context.window_manager.addosc_rate)
    elif n==4:
        text_settings.lines[4].body = bpy.context.window_manager.addosc_udp_in
    elif n==5:
        text_settings.lines[5].body = bpy.context.window_manager.addosc_udp_out
    elif n==6:
        text_settings.lines[6].body = str(int(bpy.context.window_manager.addosc_autorun))

def upd_setting_0():
    upd_settings_sub(0)
    
def upd_setting_1():
    upd_settings_sub(1)
        
def upd_setting_2():
    upd_settings_sub(2)
    
def upd_setting_3():
    upd_settings_sub(3)           

def upd_setting_4():
    upd_settings_sub(4)   

def upd_setting_5():
    upd_settings_sub(5)
    
def upd_setting_6():
    upd_settings_sub(6)
    
    
class OSC_Reading_Sending(bpy.types.Operator):
    bl_idname = "addosc.modal_timer_operator"
    bl_label = "OSCMainThread"
    
    _timer = None 
    client = "" #for the sending socket
    count = 0
    
    def upd_trick_addosc_monitor(self,context):
        upd_setting_0()
    
    def upd_trick_portin(self,context):
        upd_setting_1()
    
    def upd_trick_portout(self,context):
        upd_setting_2()
           
    def upd_trick_rate(self,context):
        upd_setting_3()
               
    def upd_trick_addosc_udp_in(self,context):
        upd_setting_4()
        
    def upd_trick_addosc_udp_out(self,context):
        upd_setting_5()

    def upd_trick_addosc_autorun(self,context):
        upd_setting_6()        
    
    bpy.types.WindowManager.addosc_udp_in  = bpy.props.StringProperty(default="127.0.0.1", update=upd_trick_addosc_udp_in, description='The IP of the interface of your Blender machine to listen on, set to 0.0.0.0 for all of them')
    bpy.types.WindowManager.addosc_udp_out = bpy.props.StringProperty(default="127.0.0.1", update=upd_trick_addosc_udp_out, description='The IP of the destination machine to send messages to')
    bpy.types.WindowManager.addosc_port_in = bpy.props.IntProperty(default=9001, min=0, max=65535, update=upd_trick_portin, description='The input network port (0-65535)')
    bpy.types.WindowManager.addosc_port_out = bpy.props.IntProperty(default=9002, min=0, max= 65535, update=upd_trick_portout, description='The output network port (0-65535)')
    bpy.types.WindowManager.addosc_rate = bpy.props.IntProperty(default=10 ,description="The refresh rate of the engine (millisecond)", min=1, update=upd_trick_rate)
    bpy.types.WindowManager.status = bpy.props.StringProperty(default="Stopped", description='Show if the engine is running or not')
    bpy.types.WindowManager.addosc_monitor = bpy.props.BoolProperty(description="Display the current value of your keys, the last message received and some infos in console", update=upd_trick_addosc_monitor)
    bpy.types.WindowManager.addosc_autorun = bpy.props.BoolProperty(description="Start the OSC engine automatically after loading a project", update=upd_trick_addosc_autorun)
    bpy.types.WindowManager.addosc_lastaddr = bpy.props.StringProperty(description="Display the last OSC address received")
    bpy.types.WindowManager.addosc_lastpayload = bpy.props.StringProperty(description="Display the last OSC message content")
    
    #modes_enum = [('Replace','Replace','Replace'),('Update','Update','Update')]
    #bpy.types.WindowManager.addosc_mode = bpy.props.EnumProperty(name = "import mode", items = modes_enum)
    
    def modal(self, context, event):
         
        if context.window_manager.status == "Stopped" :
            return self.cancel(context)	  
       
        if event.type == 'TIMER':
            #hack to refresh the GUI
            bcw = bpy.context.window_manager
            self.count = self.count + bcw.addosc_rate
            if self.count >= 500:
                self.count = 0
                if bpy.context.window_manager.addosc_monitor == True:
                    for window in bpy.context.window_manager.windows:
                        screen = window.screen
                        for area in screen.areas:
                            if area.type == 'VIEW_3D':
                                area.tag_redraw()
            
            #Reception is no more done in the timer modal operator, see the handler 

            #Sending
            sendOSC = False
            if sendOSC:
                if 'OSC_keys' in bpy.context.scene:
                    for item in bpy.context.scene.OSC_keys:
                        if item.id[0:2] == '["' and item.id[-2:] == '"]':
                            prop = eval(item.data_path+item.id)
                        else:
                            prop = eval(item.data_path+'.'+item.id)
                        
                        if str(prop) != item.value: 
                            item.value = str(prop)
                            
                            if item.idx == 0:
                                msg = osc_message_builder.OscMessageBuilder(address=item.address)
                                msg.add_arg(prop)
                                msg = msg.build()
                                self.client.send(msg)
                            
        
        return {'PASS_THROUGH'}

    def execute(self, context):
        global _report 
        bcw = bpy.context.window_manager
        
        #For sending
        try:
            self.client = udp_client.UDPClient(bcw.addosc_udp_out, bcw.addosc_port_out)
            msg = osc_message_builder.OscMessageBuilder(address="/blender")
            msg.add_arg("Hello from Blender, simple test.")
            msg = msg.build()
            self.client.send(msg)
        except OSError as err: 
            _report[1] = err
            return {'CANCELLED'}    
    
        #Setting up the dispatcher for receiving
        try:
            self.dispatcher = dispatcher.Dispatcher()
            self.dispatcher.set_default_handler(OSC_callback)
            self.server = osc_server.ThreadingOSCUDPServer((bcw.addosc_udp_in, bcw.addosc_port_in), self.dispatcher)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.start()
        except OSError as err:
            _report[0] = err
            return {'CANCELLED'}

          
        #inititate the modal timer thread
        context.window_manager.modal_handler_add(self)
        self._timer = context.window_manager.event_timer_add(bcw.addosc_rate/1000,window=context.window)
        context.window_manager.status = "Running"
        
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self._timer)
        self.server.shutdown()
        context.window_manager.status = "Stopped"
        return {'CANCELLED'}



class OSC_UI_Panel(bpy.types.Panel):
    bl_label = "AddOSC Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AddOSC"
 
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="OSC Settings:")
        row = col.row(align=True)
        row.operator("addosc.startudp", text='Start', icon='PLAY')
        row.operator("addosc.stopudp", text='Stop', icon='PAUSE')
        layout.prop(bpy.context.window_manager, 'status', text="Running Status")
        layout.prop(bpy.context.window_manager, 'addosc_udp_in', text="Listen on ")
        layout.prop(bpy.context.window_manager, 'addosc_udp_out', text="Destination address")
        col2 = layout.column(align=True)
        row2 = col2.row(align=True)
        row2.prop(bpy.context.window_manager, 'addosc_port_in', text="Input port")
        row2.prop(bpy.context.window_manager, 'addosc_port_out', text="Outport port")
        layout.prop(bpy.context.window_manager, 'addosc_rate', text="Update rate(ms)")    
        layout.prop(bpy.context.window_manager, 'addosc_autorun', text="Start at Launch")

        row = layout.row()
        row.prop(bpy.context.scene, 'addosc_defaultaddr', text="Default Address")
        row.prop(bpy.context.window_manager, 'addosc_monitor', text="Monitoring")
       
        if context.window_manager.addosc_monitor == True:
            box = layout.box()
            row5 = box.column(align=True)
            row5.prop(bpy.context.window_manager, 'addosc_lastaddr', text="Last OSC address")
            row5.prop(bpy.context.window_manager, 'addosc_lastpayload', text="Last OSC message") 

class OSC_UI_Panel2(bpy.types.Panel):
    bl_label = "AddOSC Operations"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AddOSC"
        
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=False)  
                
        col = layout.column()
        col.operator("addosc.blankprop", text='Import Blank Prop')
        
        col.label(text="Driven Properties")
        idx = 0
        if 'OSC_keys' in bpy.context.scene:
            for item in bpy.context.scene.OSC_keys:
                box = layout.box()

                row = box.row()
                row.label(text = "Prop: " + str(idx + 1))
                op = row.operator("addosc.delete",text='',icon='X')
                op.idx = idx  

                col = box.column()
                col.prop(item, 'address')

                col.prop_search(item,'data_path', bpy.data, 'objects',text='Object')
                col.prop(item,'id',text='Path', icon='RNA')

                col.prop(item, 'osc_type', text='Type')
            
                col.prop(item, 'idx', text='Index')
                idx += 1
                if bpy.context.window_manager.addosc_monitor == True:
                    col.prop(item, 'value')
                         
class StartUDP(bpy.types.Operator):
    bl_idname = "addosc.startudp"
    bl_label = "Start UDP Connection"
    bl_description ="Start the OSC engine"
 
    def execute(self, context):
        global _report
        if context.window_manager.addosc_port_in == context.window_manager.addosc_port_out:
            self.report({'INFO'}, "Ports must be different.")
            return{'FINISHED'} 
        if bpy.context.window_manager.status != "Running" :
            bpy.ops.addosc.modal_timer_operator()
            if _report[0] != '':
                self.report({'INFO'}, "Input error: {0}".format(_report[0]))
                _report[0] = ''
            elif _report[1] != '':
                self.report({'INFO'}, "Output error: {0}".format(_report[1]))
                _report[1] = ''                
        else:
            self.report({'INFO'}, "Already connected !")	  
        return{'FINISHED'}

class StopUDP(bpy.types.Operator):
    bl_idname = "addosc.stopudp"
    bl_label = "Stop UDP Connection"
    bl_description ="Stop the OSC engine"
 
    def execute(self, context):
        self.report({'INFO'}, "Disconnected !")
        bpy.context.window_manager.status = "Stopped"
        return{'FINISHED'}

class PickOSCaddress(bpy.types.Operator):
    bl_idname = "addosc.pick"
    bl_label = "Pick the last event OSC address"
    bl_options = {'UNDO'}
    bl_description ="Pick the address of the last OSC message received"
   
    i_addr = bpy.props.StringProperty()  
 
    def execute(self, context):
        last_event = bpy.context.window_manager.addosc_lastaddr
        if len(last_event) > 1 and last_event[0] == "/": 
            for item in bpy.context.scene.OSC_keys:
                if item.address == self.i_addr :
                    item.address = last_event
        return{'FINISHED'}
    
class AddOSC_ImportBlank(bpy.types.Operator):
    bl_idname = "addosc.blankprop"  
    bl_label = "Import a blank prop"
    bl_options = {'UNDO'}
    bl_description ="Import the keys of the active Keying Set"
    
    def verifdefaddr(self,context):
        if context.scene.addosc_defaultaddr[0] != "/":
            context.scene.addosc_defaultaddr = "/"+context.scene.addosc_defaultaddr
    
    bpy.types.Scene.addosc_defaultaddr = bpy.props.StringProperty(default="/blender", description='Form new addresses based on this keyword',update=verifdefaddr)

    def execute(self, context):
        if 'OSC_keys' not in bpy.context.scene:
            bpy.context.scene.OSC_keys.add()
            bpy.context.scene.OSC_keys_tmp.add()

        ks = bpy.context.scene.keying_sets.active
        
        item = bpy.context.scene.OSC_keys.add()
        item.id = "location[0]"
        item.address = "/blender/0"
        item.idx = 0
                                                     
        return{'FINISHED'}        

class AddOSC_Delete(bpy.types.Operator):
    bl_idname = "addosc.delete"  
    bl_label = "Remove a Key"
    bl_options = {'UNDO'}
    bl_description ="Remove a Key"

    idx = IntProperty()

    def execute(self, context):
        if 'OSC_keys' in bpy.context.scene:
            keys = bpy.context.scene.OSC_keys

        keys.remove(self.idx) 
        context.area.tag_redraw()                     
        return{'FINISHED'}     