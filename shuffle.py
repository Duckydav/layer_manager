# ----------------------------------------------------------------------------------------------------------
# Shuffle auto v1.2
# Author: David Francois
# Copyright (c) 2024, David Francois
# ----------------------------------------------------------------------------------------------------------

import nuke
from PySide2.QtCore import QTimer

# Define the timer and double-click state
click_timer = QTimer()
click_timer.setSingleShot(True)  # Ensure the timer is in singleShot mode
is_double_click = False
knob_callback_short = None  # Callback for single-click updates
knob_callback_long = None   # Callback for double-click updates

# Connect to the timer for single-click
click_timer.timeout.connect(lambda: single_click())

# ----------------------------------------------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------------------------------------------

def is_shuffle_node(node):
    return node.Class() == "Shuffle"

def is_shuffle2_node(node):
    return node.Class() == "Shuffle2"

# ----------------------------------------------------------------------------------------------------------
# Callback management
# ----------------------------------------------------------------------------------------------------------

def setup_short_callback(node):
    global knob_callback_short
    def knob_changed_callback_short():
        to_label_short(node)
    remove_short_callback(node)
    knob_callback_short = knob_changed_callback_short
    nuke.addKnobChanged(knob_callback_short, node=node)

def setup_long_callback(node):
    global knob_callback_long
    def knob_changed_callback_long():
        to_label(node)
    remove_long_callback(node)
    knob_callback_long = knob_changed_callback_long
    nuke.addKnobChanged(knob_callback_long, node=node)

def remove_short_callback(node):
    global knob_callback_short
    if knob_callback_short:
        nuke.removeKnobChanged(knob_callback_short, node=node)
        knob_callback_short = None

def remove_long_callback(node):
    global knob_callback_long
    if knob_callback_long:
        nuke.removeKnobChanged(knob_callback_long, node=node)
        knob_callback_long = None

# ----------------------------------------------------------------------------------------------------------
# Click handlers
# ----------------------------------------------------------------------------------------------------------

def get():
    """
    This function is called on a double-click and applies the long label.
    """
    try:
        node = nuke.selectedNode()
    except:
        nuke.message("Please select a Shuffle or Shuffle2")
        return

    if is_shuffle_node(node):
        to_label(node)
    elif is_shuffle2_node(node):
        to_label(node)

    # Ensure the short callback is removed, and apply long label
    remove_short_callback(node)
    to_label(node)  # Call to_label on double-click
    setup_long_callback(node)  # Setup long callback if needed for double-click

def get_short():
    """
    This function is called on a single-click and applies the short label.
    """
    try:
        node = nuke.selectedNode()
    except:
        nuke.message("Please select a Shuffle or Shuffle2")
        return

    if is_shuffle_node(node):
        to_label_short(node)
    elif is_shuffle2_node(node):
        to_label_short(node)

    # Ensure the long callback is removed, and apply short label
    remove_long_callback(node)
    to_label_short(node)  # Call to_label_short on single-click
    setup_short_callback(node)  # Setup short callback for dynamic updates on single-click

def single_click():
    """
    Function to handle single click, calling the short label function.
    """
    global is_double_click
    if not is_double_click:
        get_short()
    is_double_click = False

def double_click():
    """
    Function to handle double-click, calling the long label function.
    """
    global is_double_click
    get()
    is_double_click = False

def run():
    """
    Entry point function that handles both single and double clicks.
    """
    global is_double_click
    if click_timer.isActive():
        is_double_click = True
        click_timer.stop()
        double_click()
    else:
        click_timer.start(500)


# ----------------------------------------------------------------------------------------------------------
# Processing functions
# ----------------------------------------------------------------------------------------------------------

def process_shuffle2(node, short_label=False):
    mappings = node["mappings"].value()
    label = ""
    input = ['A', 'B']

    def index(value):
        if "{" in value and "}" in value:
            return int(value.split("{")[1].split("}")[0])
        return 0

    fromInput1 = input[1 - index(node['fromInput1'].value())]
    fromInput2 = input[1 - index(node['fromInput2'].value())]

    channel_shortcuts = {
        "red": "r",
        "green": "g",
        "blue": "b",
        "alpha": "a",
        "black": "0",
        "white": "1",
    }

    connections = {"A": {}, "B": {}}
    for mapping in mappings:
        if mapping[0] == -1 and mapping[1] == 'black':
            continue

        for channel in channel_shortcuts:
            if mapping[1].endswith(f".{channel}"):
                input_key = fromInput1 if mapping[0] == 0 else fromInput2
                input_layer = mapping[1].split('.')[0]
                in_channel = channel_shortcuts[channel]
                output_layer = mapping[2].split('.')[0]
                out_channel = channel_shortcuts[mapping[2].split('.')[-1]]

                if input_layer not in connections[input_key]:
                    connections[input_key][input_layer] = {"in_channels": "", "out_channels": {}}
                connections[input_key][input_layer]["in_channels"] += in_channel
                if output_layer not in connections[input_key][input_layer]["out_channels"]:
                    connections[input_key][input_layer]["out_channels"][output_layer] = ""
                connections[input_key][input_layer]["out_channels"][output_layer] += out_channel

    for input_key in ["B", "A"]:
        layers = connections[input_key]
        for input_layer, details in layers.items():
            in_channels = details["in_channels"]
            for output_layer, out_channels in details["out_channels"].items():
                input_display = input_layer if input_layer != "rgba" else in_channels
                output_display = out_channels if output_layer == "rgba" else output_layer
                if short_label:
                    label += f"{input_display}={output_display}\n"
                # else:
                #     label += f"{input_key}➞{input_display} = {output_display}\n"

    return label.strip()

#TODO introduire de short label
def process_shuffle(node, short_label=False):
    channel_shortcuts = {
        "red": "r",
        "green": "g",
        "blue": "b",
        "alpha": "a",
        "black": "0",
        "white": "1",
        "X": "x",
        "Y": "y",
        "Z": "z",
        "u": "u",
        "v": "v",
        "front": "front",
        "back": "back"
    }

    input_layer = node["in"].value()
    output_layer = node["out"].value()

    if input_layer == "none" or output_layer == "none":
        return "in or out is set to 'none'"

    mapped_channels = ""
    for out_channel in ["red", "green", "blue", "alpha"]:
        input_source = node[out_channel].value()
        mapped_channels += channel_shortcuts[input_source]

    # label = f"{mapped_channels} = {output_layer}"
    label = f"{input_layer} = {output_layer}"
    return label.strip()

# ----------------------------------------------------------------------------------------------------------
# Label functions
# ----------------------------------------------------------------------------------------------------------

def to_label(node):
    if is_shuffle2_node(node):
        label = process_shuffle2(node)
    elif is_shuffle_node(node):
        label = process_shuffle(node)
    node['label'].setValue(label)

def to_label_short(node):
    if is_shuffle2_node(node):
        label = process_shuffle2(node, short_label=True)
    elif is_shuffle_node(node):
        label = process_shuffle(node, short_label=True)
    node['label'].setValue(label)
