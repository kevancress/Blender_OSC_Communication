import bpy
from bpy.props import IntProperty, EnumProperty, StringProperty, CollectionProperty
from bpy.types import PropertyGroup

def update_num_props(self,context):
    prefix = self
    props = prefix.props
    currentProps = len(props)
    numProps = self.numProps

    # Add or remove props untill matching
    if numProps > currentProps:
        while numProps > len(props):
            prefix.props.add()
    elif numProps < currentProps:
        while numProps < len(props):
            prefix.props.remove(len(props)-1)



class BaseProp:
    data_path: StringProperty(name="Data path", default="")
    id: StringProperty(name="ID", default="")
    osc_type: StringProperty(name="Type", default="Unknown")
    value: StringProperty(name="Value", default="Unknown")
    idx: IntProperty(name="Index", min=0, default=0)

# For Simple Adress -> Prop Mappings
class SceneSettingItem(PropertyGroup,BaseProp):
    address: StringProperty(name="Address", default="")

bpy.utils.register_class(SceneSettingItem) 

class PropItem(PropertyGroup,BaseProp):
    dummy_prop: StringProperty(name="I Just need somthing here, I'll do somthing neat with it later", default="")

bpy.utils.register_class(PropItem) 

# Defines the Message Prefix and Number of Properties
class PrefixItem(PropertyGroup):
    prefix = StringProperty(name="Prefix", default="")
    numProps = IntProperty(name="Number of Properties", min=0, max = 15, default=0, update= update_num_props)

    props: CollectionProperty(type=PropItem)
    
bpy.utils.register_class(PrefixItem) 

# Defines the Message Format and Address
class MessageParser (PropertyGroup):
    messageType: EnumProperty(
                items=(('01', "Space Seperated String", "Space Seperated String"),
                        ('02', "NOT IMPLIMENTED", "Reserved for implimentation of other Message Formats")),
                name="Message Type",
                description="Message Type")  

    messageAddress: StringProperty(name="Address", default="")

    prefixes: CollectionProperty(type=PrefixItem)

bpy.utils.register_class(MessageParser)


def draw_parser(layout,idx,parser):
    box = layout.box()
    row = box.row()
    row.label(text = "Message Parser " + str(idx + 1))
    op = row.operator("addosc.delete_parser",text='',icon='X')
    op.idx = idx 

    col = box.column()
    col.prop(parser, "messageAddress", text="Address")
    col.prop(parser, "messageType", text="Type")
    op = col.operator("addosc.parser_prefix",icon='FILE_TEXT')
    op.idx = idx 

    if len(parser.prefixes) > 0:
        prefix_idx = 0
        for prefix in parser.prefixes:
            draw_prefix(box,idx,prefix_idx,prefix)
            prefix_idx +=1
        

def draw_prefix(layout,parser_idx,prefix_idx,prefix):
    row = layout.row()
    row.label(text='Prefix:' + str(prefix_idx+1))
    op = row.operator("addosc.delete_prefix",text='',icon='X')
    op.idx = parser_idx  
    op.prefix_idx = prefix_idx 
    
    row = layout.row(align=True)
    row.prop(prefix, 'prefix', text ='Prefix')
    row.prop(prefix, 'numProps' , text='')

    if len(prefix.props) > 0:
        prop_idx = 0
        for prop in prefix.props:
            draw_prop(layout,prop_idx,prop)
            prop_idx +=1


def draw_prop(layout,prop_idx,prop):
    box = layout.box()
    box.label(text='Property ' + str(prop_idx+1))

    row = box.row()

    col = box.column()
    row = col.row()
    split = row.split(factor=0.8)
    split.prop(prop,'data_path',text='Path')
    split.prop(prop,'id',text='')

    col.prop(prop, 'osc_type', text='Type')

class OSC_UI_Panel3(bpy.types.Panel):
    bl_label = "OSC Message Parser"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AddOSC"
        
    def draw(self, context):
        layout = self.layout
        row = layout.row(align=False)
        row.operator("addosc.parser", text='Add OSC Parser')

        col = layout.column()
        col.label(text="OSC Parsers")
        if 'OSC_Parsers' in bpy.context.scene:
            idx = 0
            for parser in bpy.context.scene.OSC_Parsers:
                draw_parser(layout,idx,parser)
                idx += 1
 
class AddOSC_Parser(bpy.types.Operator):
    bl_idname = "addosc.parser"  
    bl_label = "Create a Message Parser"
    bl_options = {'UNDO'}
    bl_description ="Creates a Message Parser for Space Seperated Strings"
    
    def execute(self, context):
        if 'OSC_Parsers' not in bpy.context.scene:
            bpy.types.Scene.OSC_Parsers = CollectionProperty(type=MessageParser)

        parser = bpy.context.scene.OSC_Parsers.add()

                                                     
        return{'FINISHED'}        

class AddOSC_Parser_Prefix(bpy.types.Operator):
    bl_idname = "addosc.parser_prefix"  
    bl_label = "Create a Message Prefix"
    bl_options = {'UNDO'}
    bl_description ="Creates a Message Parser for Space Seperated Strings"
    
    idx = IntProperty()

    def execute(self, context):
        parsers = bpy.context.scene.OSC_Parsers
        parentParser = parsers[self.idx]

        newPrefix = parentParser.prefixes.add()

                                                        
        return{'FINISHED'}        
        
class AddOSC_Delete_Parser(bpy.types.Operator):
    bl_idname = "addosc.delete_parser"  
    bl_label = "Remove a Key"
    bl_options = {'UNDO'}
    bl_description ="Remove a Key"

    idx = IntProperty()

    def execute(self, context):
        if 'OSC_Parsers' in bpy.context.scene:
            parsers = bpy.context.scene.OSC_Parsers

        parsers.remove(self.idx) 
        context.area.tag_redraw()                     
        return{'FINISHED'}   

    
class AddOSC_Delete_Prefix(bpy.types.Operator):
    bl_idname = "addosc.delete_prefix"  
    bl_label = "Remove a Prefix"
    bl_options = {'UNDO'}
    bl_description ="Remove a Prefix"

    idx = IntProperty()
    prefix_idx = IntProperty()

    def execute(self, context):
        if 'OSC_Parsers' in bpy.context.scene:
            parsers = bpy.context.scene.OSC_Parsers

        parsers[self.idx].prefixes.remove(self.prefix_idx)
        context.area.tag_redraw()                     
        return{'FINISHED'}   
