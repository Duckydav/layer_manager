#------------------------------------------------------------------------------#
#-------------------------------------------------------------------- HEADER --#

"""
:synopsis:
    Script to control the GradePass node

"""

#------------------------------------------------------------------------------#
#------------------------------------------------------------------- IMPORTS --#

# built-in

# third party
import nuke

# external

# internal

import node_utils
import position_utils as move


# ---------------------------------------------------------------------------- #
# ----------------------------------------------------------------- GLOBALS -- #

DEFAULT_COLOR = 25599999
WARNING_COLOR = 2610898687
ERROR_COLOR = 2671189247

#------------------------------------------------------------------------------#
#----------------------------------------------------------------- CALLBACKS --#


def knobChanged():
    n = nuke.thisNode()
    k = nuke.thisKnob()
    if nuke.GUI:
        if k.name() == "settings_mask_isolate_check":
            if n[k.name()].value():
                n["tile_color"].setValue(WARNING_COLOR)
            else:
                n["tile_color"].setValue(DEFAULT_COLOR)

        if "_out" in k.name():
            if "RGBA_" in n[k.name()].value() or n[k.name()].value() == "none":
                n["tile_color"].setValue(DEFAULT_COLOR)
                n["disable"].setValue(False)
            else:
                n["tile_color"].setValue(ERROR_COLOR)
                n["disable"].setValue(True)

def layer_knobChanged():
    n = nuke.thisNode()
    parent_node = nuke.thisParent()
    k = nuke.thisKnob()
    if k.name() == "Achannels":
        if "RGBA_" in n[k.name()].value() or n[k.name()].value() == "none":
            parent_node["tile_color"].setValue(DEFAULT_COLOR)
            parent_node["disable"].setValue(False)
        else:
            parent_node["tile_color"].setValue(ERROR_COLOR)
            parent_node["disable"].setValue(True)

#------------------------------------------------------------------------------#
#----------------------------------------------------------------- FUNCTIONS --#

class NodeCoord(object):
    """
    Main class object to get basic node coordination information
    """
    def __init__(self, node):
        if node.screenWidth == 0:
            nuke.autoplaceSnap(node)
        self.width = node.screenWidth()
        self.height = node.screenHeight()
        self.x = node["xpos"].value()
        self.y = node["ypos"].value()
        if nuke.GUI:
            self.cent_x = self.x + (self.width // 2)
            self.cent_y = self.y + (self.height // 2)

def add_layer():
    """This will add an entry to let the user chose a layer to grade"""
    # Get this node
    for node in nuke.allNodes():
        node['selected'].setValue(False)
    n = nuke.thisNode()

    # Get current layer name and +1 for next layer
    layer_count = n["layer_count"].value()

    # Check to limit the layer to 10 since some artist abuse it !
    if layer_count >= 11:
        nuke.message("No Dayne.... No!")
        return

    layer_name = "layer_{}".format(int(layer_count))
    n["layer_count"].setValue(layer_count + 1)

    # Get builders node and their top node
    out_builder_node = nuke.toNode("out_builder_dot")
    out_builder_top_node = out_builder_node.input(0)

    graded_builder_node = nuke.toNode("graded_builder_dot")
    graded_builder_top_node = graded_builder_node.input(0)

    in_builder_node = nuke.toNode("in_builder_dot")
    in_builder_top_node = in_builder_node.input(0)

    ### CREATE MERGE OUT NODEs
    # Create Nodes
    merge_out_node = create_node("Merge2")
    merge_out_node["name"].setValue("{0}_out".format(layer_name))
    merge_out_node["operation"].setValue("plus")
    merge_out_node["Achannels"].setValue("none")
    merge_out_node["output"].setValue("rgb")
    merge_out_node["knobChanged"].setValue("from nuke_tools.gizmos.scripts import rfxGrade\n"
                                           "rfxGrade.layer_knobChanged()")

    # flag it
    merge_out_node["Achannels"].setFlag(0x00000001) #no checkmarks
    merge_out_node["Achannels"].setFlag(0x00000002) #no alpha

    # Move it
    under(merge_out_node, out_builder_top_node, offset=24)

    # Connect it
    merge_out_node.setInput(0, out_builder_top_node)
    merge_out_node.setInput(1, out_builder_top_node)
    out_builder_node.setInput(0, merge_out_node)

    ### CREATE MERGE IN NODES
    # Create it
    merge_in_node = create_node("Merge2")
    merge_in_node["name"].setValue("{0}_in".format(layer_name))
    merge_in_node["operation"].setValue("copy")
    merge_in_node["Achannels"].setExpression("{0}.Achannels".format(merge_out_node.name()))
    merge_in_node["Bchannels"].setValue("none")

    # Expressions
    merge_in_node["output"].setExpression("{0}.Achannels".format(merge_out_node.name()))
    merge_in_node["disable"].setExpression("{0}.disable".format(merge_out_node.name()))

    # Flag it
    merge_in_node["Achannels"].setFlag(0x00000001)
    merge_in_node["Achannels"].setFlag(0x00000002)
    merge_in_node["output"].setFlag(0x00000001)
    merge_in_node["output"].setFlag(0x00000002)

    merge_in_dot = create_node("Dot")
    merge_in_dot["name"].setValue("{0}_dot".format(layer_name))

    # Move it
    under(merge_in_node, in_builder_top_node, offset=24)
    under(merge_in_dot, graded_builder_top_node, offset=24)

    # Connect it
    merge_in_node.setInput(1, merge_in_dot)
    merge_in_node.setInput(0, in_builder_top_node)
    in_builder_node.setInput(0, merge_in_node)
    merge_in_dot.setInput(0, graded_builder_top_node)
    graded_builder_node.setInput(0, merge_in_dot)


    ### CREATE UI ENTRY
    # Name it
    layer_link_name = "{0}_link".format(layer_name)

    # Create it

    layer_link_knob = nuke.Link_Knob("")
    layer_link_knob.setName(layer_link_name)
    layer_link_knob.setLabel("<font size=3 color=White>Layer:")
    layer_link_knob.setValue("none")

    # Link it
    layer_link_knob.makeLink(merge_out_node.name(), "Achannels")

    # Autolabel entry
    layer_link_autolabel = '+ nuke.thisNode()["{0}"].value()'.format(layer_link_name)

    # Remove Button
    remove_knob = nuke.PyScript_Knob("{0}_remove".format(layer_name), "X")
    remove_knob.setLabel("<font size=3 color=White>X")
    remove_knob.setValue("layer_link_autolabel= '{0}'\n"
                          "remove_layer('{1}', layer_link_autolabel)".format(layer_link_autolabel,
                                                                                      layer_name))
    remove_knob.clearFlag(nuke.STARTLINE)

    # Mute knob
    mute_knob = nuke.PyScript_Knob("{0}_mute".format(layer_name), "mute")
    mute_knob.setValue("mute_layer('{0}')".format(layer_name))
    mute_knob.setLabel("<font size=3 color=White>Mute")

    # Reorder knobs to insert them at the correct position
    knob_list = list(n.knobs().keys())
    insert_index = knob_list.index("aovs_layers_text") + 1

    # Temporarily remove all knobs after the insertion point
    knobs_to_readd = []
    for i in range(insert_index, len(knob_list)):
        knob_name = knob_list[i]
        knobs_to_readd.append(n.knobs()[knob_name])
        n.removeKnob(n.knobs()[knob_name])


    # Add knobs
    n.addKnob(layer_link_knob)
    n.addKnob(remove_knob)
    n.addKnob(mute_knob)

    for knob in knobs_to_readd:
        n.addKnob(knob)

    ### AUTOLABEL
    # check if there is already an autolabel.
    # If yes, take the current state of autolable knob instead of the node name
    node_name = "nuke.thisNode().name() + \"\\n\" + nuke.thisNode()['settings_label_input'].value()"
    if n["autolabel"].value():
        node_name = n["autolabel"].value()

    #set the autolabel field with the updated link name
    n['autolabel'].setValue("{0} {1}".format(node_name, "+ \"\\n\" {0}".format(layer_link_autolabel)))

def onCreate():
    n = nuke.thisNode()
    knobs = n.knobs()
    for knob in knobs:
        if "_link" in knob:
            if "RGBA_" in n[knob].value() or n[knob].value() == "none":
                n["tile_color"].setValue(DEFAULT_COLOR)
                n["disable"].setValue(False)
            else:
                n["tile_color"].setValue(ERROR_COLOR)
                n["disable"].setValue(True)

def create_node(node_type, title=None, **kwargs):
    node = nuke.createNode(node_type, inpanel=False)
    node["selected"].setValue(False)

    add_knob_value(node, **kwargs)

    if title:
        add_label(node, title)
    return node

def add_label(node, label):
    node["autolabel"].setValue("'{}' + \"\\n\" + nuke.thisNode().name()".format(label))

def basic_move(node, target, x=0, y=0):
    """base function for moving nodes relative to each other. node_one is
    always relative to node_two
    """
    target_coord = NodeCoord(target)
    node_coord = NodeCoord(node)
    x_axis = (target_coord.cent_x - (node_coord.width // 2)) + x
    y_axis = (target_coord.cent_y - (node_coord.height // 2)) + y
    node["xpos"].setValue(x_axis)
    node["ypos"].setValue(y_axis)

def under(node, target, offset=100):
    basic_move(node, target, y=offset)

def remove_layer(layer_name, autolabel):
    " function to delete entry in the node"
    # Get this node
    n = nuke.thisNode()

    # Update autolabel
    autolabel_list = n["autolabel"].value()
    new_list = autolabel_list.replace("+ \"\\n\" {0}".format(autolabel), "")
    n["autolabel"].setValue(new_list)

    # Remove knobs
    n.removeKnob(n.knobs()["{0}_mute".format(layer_name)])
    n.removeKnob(n.knobs()["{0}_link".format(layer_name)])
    n.removeKnob(n.knobs()["{0}_remove".format(layer_name)])
    # Remove node
    nodes = nuke.allNodes()
    for node in nodes:
        if layer_name in node.name():
            nuke.delete(node)

def clear_all():
    remove_buttons = [r for r in nuke.thisNode().knobs() if '_remove' in r]
    for r in remove_buttons:
        nuke.thisNode()[r].execute()
        nuke.thisNode()["layer_count"].setValue(0)

def mute_layer(layer_name):
    node = nuke.thisNode()
    merge_node = nuke.toNode("{0}_out".format(layer_name))
    node_state = merge_node["disable"].value()
    if node_state:
        node["{0}_mute".format(layer_name)].setLabel("<font size=3 color=White>Mute")
        node["{0}_link".format(layer_name)].setEnabled(True)
        merge_node["disable"].setValue(0)
    else:
        node["{0}_mute".format(layer_name)].setLabel("<font size=3 color=Red>Mute")
        node["{0}_link".format(layer_name)].setEnabled(False)
        merge_node["disable"].setValue(1)

def clear_muted():
    n = nuke.thisNode()
    nodes = nuke.allNodes()
    for node in nodes:
        if "_out" in node.name():
            node["disable"].setValue(0)
            node["Achannels"].setEnabled(True)
            n[node.name().replace("_out", "_mute")].setLabel("<font size=3 color=White>Mute")

