# ----------------------------------------------------------------------------------------------------------
# Layer Manager v1.3
# Author: David Francois
# Copyright (c) 2024, David Francois
# ----------------------------------------------------------------------------------------------------------

"""

@description:
This tool provides a user-friendly interface for quickly visualizing Viewer Layer Channels with a single click.
    It also enables the addition of a GradeAOV layer with a second click when selecting a Light Layer.

    Features:
    - Efficiently navigate through available layers
    - Easily create GradeAOV, Shuffle, and Contribution nodes
    - Customizable sections and preferences for better organization
"""

# ----------------------------------------------------------------------------#
# ----------------------------------------------------------------- IMPORTS --#


import nuke
import os
import json
import math
import shuffle
import gradepass
import contribution


from PySide2.QtWidgets import QApplication, QWidget, QHBoxLayout, QListWidget, \
    QListWidgetItem, QFrame, QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QColor



class LayerSelector(QListWidget):

    """
    A custom QListWidget for managing and interacting with layers.

    Features:
    - Keyboard shortcuts for quick navigation and actions
    - Mouse interactions for selection and layer operations
    - Custom styles and dynamic updates
    """

    keyPressed = Signal(int)
    ctrlClicked = Signal(QListWidgetItem)
    shiftClicked = Signal(QListWidgetItem)
    shiftCtrlClicked = Signal(QListWidgetItem)
    altClicked = Signal(QListWidgetItem)
    ctrlPressed = Signal(bool)
    shiftPressed = Signal(bool)
    rowChanged = Signal(int)
    is_empty_layer_present = False

    def __init__(self, parent=None):
        super(LayerSelector, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        current_row = self.currentRow()

        if event.key() == Qt.Key_G:
            self.keyPressed.emit(event.key())
        elif event.key() == Qt.Key_Up:
            new_row = max(0, current_row - 1)
            self.setCurrentRow(new_row)
            self.rowChanged.emit(new_row)
        elif event.key() == Qt.Key_Down:
            new_row = min(self.count() - 1, current_row + 1)
            self.setCurrentRow(new_row)
            self.rowChanged.emit(new_row)
        elif event.key() == Qt.Key_Shift:
            self.shiftPressed.emit(True)
        elif event.key() == Qt.Key_Control:
            self.ctrlPressed.emit(True)
        else:
            super(LayerSelector, self).keyPressEvent(event)


    def keyReleaseEvent(self, event):
        super(LayerSelector, self).keyReleaseEvent(event)
        if event.key() == Qt.Key_Shift:
            self.shiftPressed.emit(False)
        elif event.key() == Qt.Key_Control:
            self.ctrlPressed.emit(False)

    def mousePressEvent(self, event):
        if self.is_empty_layer_present:
            return
        super(LayerSelector, self).mousePressEvent(event)
        item = self.itemAt(event.pos())
        if item:
            if event.button() == Qt.LeftButton and QApplication.keyboardModifiers() == Qt.ControlModifier:
                self.ctrlClicked.emit(item)
            elif event.button() == Qt.LeftButton and QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self.shiftClicked.emit(item)
            elif event.button() == Qt.LeftButton and QApplication.keyboardModifiers() == (Qt.ShiftModifier | Qt.ControlModifier):
                self.shiftCtrlClicked.emit(item)


    def setStyleSheet(self, styleSheet):
        for index in range(self.count()):
            item = self.item(index)
            item.setBackground(QColor('orange'))
            item.setForeground(QColor('black'))
        super(LayerSelector, self).setStyleSheet(styleSheet)

    def add_layer_to_list(self, layer_name, custom):
        if not custom:
            layer_name = "!!! Layer Empty !!!"
        item = QListWidgetItem(layer_name)
        self.addItem(item)


class PreferencesDialog(QDialog):

    """
    PreferencesDialog class for configuring layer management preferences.

    This dialog provides a user-friendly interface to customize the behavior of the Layer Manager.

    Features:
    - Modify keywords for categorizing layer into sections (Light, Mask, Tech, Utility, Custom)
    - Set a custom title for the 'Custom Layer' section
    - Define exclusion keywords to hide specific layers
    - Load and save preferences to ~/.nuke/layermanager_preferences.json
    - Provide explanatory text and an intuitive interface for easy configuration

    Sections:
    1. Layer Layer: Configure keywords for each Layer category
    2. General Settings: Define exclusion keywords

    The preferences are saved in a JSON file and reloaded when the dialog is reopened.
    """

    def __init__(self, parent=None):
        super(PreferencesDialog, self).__init__(parent)
        self.setWindowTitle("Preferences")
        self.resize(400, 400)

        # Initialize preferences
        self.preferences = {
            "Exclusion Keywords": [],

            "Light Layer": [],
            "Mask Layer": [],
            "Tech Layer": [],
            "Utility Layer": [],
            "custom Layer": [],
            "custom Title": ""
        }
        self.text_fields = {}
        self.filepath = os.path.join(os.path.expanduser("~"), ".nuke", "layermanager_preferences.json")
        self.load_preferences()


        layout = QVBoxLayout()

        line_above_save = QFrame()
        line_above_save.setFrameShape(QFrame.HLine)
        line_above_save.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_above_save)

        # SECTION 1 : Layer
        layer_title = QLabel()
        layer_title.setText(
            '<p align="center" style="font-size: 16px; font-weight: bold; color: #FCB132; margin: 0;">'
            'Layer <span style="color: #FFFFFF;">Manager</span>'
            '</p>'
        )
        layout.addWidget(layer_title)

        line_above_save = QFrame()
        line_above_save.setFrameShape(QFrame.HLine)
        line_above_save.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_above_save)
        # Explanatory text
        explanation_label = QLabel()
        explanation_label.setText(
            '<p style="font-size: 11px; color: #A2A1A1; font-style: italic; text-align: justify; line-height: 2.5;">'
            '<ul style="list-style-type: disc; margin-left: 20px; padding-left: 0;">'
            '<li>'
            'Define the keywords for each section of the Layer:<br>'
            '<b>Light Layer</b>, <b>Mask Layer</b>, <b>Utility Layer</b>, <b>Custom Layer</b>, & <b>Tech Layer</b>.'
            '</li>'
            '<li>'
            'The <b>Tech Layer</b> will be the default section if no words are specified.'
            '</li>'
            '<li>'
            'You can also customize the title of the <b>Custom Layer</b>.'
            '</li>'
            '<li>'
            'Exclude unnecessary layers from the Layer Manager, such as Cryptomatte.'
            '</li>'
            '<li>'
            '</li>'
            '</ul>'
            '</p>'
        )
        layout.addWidget(explanation_label)

        line_above_save = QFrame()
        line_above_save.setFrameShape(QFrame.HLine)
        line_above_save.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_above_save)

        # Add fields for the "Layer" section
        for section in ["Light Layer", "Mask Layer", "Tech Layer", "Utility Layer", "custom Layer", "custom Title"]:
            self.add_preference_field(section, layout)

        line_above_save = QFrame()
        line_above_save.setFrameShape(QFrame.HLine)
        line_above_save.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_above_save)


        # SECTION 2 : General
        general_title = QLabel()
        general_title.setText(
            '<p align="center" style="font-size: 16px; font-weight: bold; color: #FCB132; margin: 0;">'
            'General <span style="color: #FFFFFF;">Settings</span>'
            '</p>'
        )
        layout.addWidget(general_title)

        line_above_save = QFrame()
        line_above_save.setFrameShape(QFrame.HLine)
        line_above_save.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_above_save)


        # Add fields for the "General" section
        for section in ["Exclusion Keywords"]:
            self.add_preference_field(section, layout)

        line_above_save = QFrame()
        line_above_save.setFrameShape(QFrame.HLine)
        line_above_save.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_above_save)

        # Button to save preferences
        save_button = QPushButton("Save Preferences")
        save_button.clicked.connect(self.save_preferences)
        layout.addWidget(save_button)

        # Separation line below the "Save Preferences" button
        line_below_save = QFrame()
        line_below_save.setFrameShape(QFrame.HLine)
        line_below_save.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_below_save)

        # Add an Qlabel for credits below the "Save Preferences" button
        credits_label = QLabel()
        credits_label.setText(
            '<p align="center">'
            '<a href="https://github.com/Duckydav" style="text-decoration:none; color:#A2A1A1">'
            'Viewer<b><font color="#545454"> Layer</font></b> v01.2 &copy; 2024'
            '</a>'
            '</p>'
        )
        credits_label.setOpenExternalLinks(True)
        credits_label.setStyleSheet("font-size: 12px; color: #bbbbbb;")
        layout.addWidget(credits_label)

        self.setLayout(layout)

    def add_preference_field(self, section, layout):
        """Add a text field for a specific section."""
        if section == "Grade AOV Node":
            label = QLabel("GradeAOV to Layer")
        else:
            label = QLabel(f"{section}")
        label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(label)

        # Text field
        text_field = QLineEdit(
            ", ".join(self.preferences[section])
            if isinstance(self.preferences[section], list)
            else self.preferences[section]
        )
        layout.addWidget(text_field)
        self.text_fields[section] = text_field

        # Add an explanation under the text field if it is "grade AOV node"
        if section == "Garde AOV Node":
            explanation = QLabel(
                "<i>Choose GradeAOV's name from your folder .nuke/ToolSets </i>"
            )
            explanation.setStyleSheet("color: #bbbbbb; font-size: 12px; margin-bottom: 10px;")
            layout.addWidget(explanation)

        # Add a space to separate visually
        spacer = QLabel(" ")
        layout.addWidget(spacer)

    def load_preferences(self):
        """Load preferences from a JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as file:
                    self.preferences = json.load(file)


            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load preferences: {e}")
        else:
            # Initialize with default values if the file does not exist
            self.preferences = {
                "Exclusion Keywords": [],
                "Garde AOV Node": "",
                "Light Layer": [],
                "Mask Layer": [],
                "Tech Layer": [],
                "Utility Layer": [],
                "custom Layer": [],
                "custom Title": "custom"
            }

        # Check that "Custom Title" is defined and not empty
        if not self.preferences.get("custom Title"):
            self.preferences["custom Title"] = "custom"

    def save_preferences(self):
        """Save preferences to a JSON file and reload preferences."""
        try:
            with open(self.filepath, 'w') as file:
                for section, text_field in self.text_fields.items():
                    if section == "custom Title":
                        self.preferences[section] = text_field.text().strip() or "custom"

                    else:
                            # Save other preferences in the form of a list
                            self.preferences[section] = [kw.strip() for kw in text_field.text().split(",")]

                # Save preferences in the JSON file
                json.dump(self.preferences, file, indent=4)

            # Reload preferences after backup
            self.load_preferences()
            print("Preferences saved successfully.")
            nuke.message("Preferences saved successfully.")
            self.close()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save preferences: {e}")


class LayerManagerUI(QWidget):

    """
    LayerManagerUI class for visualizing and managing layer channel in Nuke.

    This class provides an interactive interface to navigate between different layer sections,
    create nodes like GradeAOV, Shuffle, Shuffle2, and Contribution with ease, and generate
    a contact sheet of available layers.

    Features:
    - Dynamic display of layers grouped into sections defined in preferences
    - Keyboard shortcuts for quick navigation and node creation
    - Mouse interactions (Ctrl+Click, Shift+Click) to trigger actions based on context
    - Automatic RGBA reset on closure
    - Built-in preferences dialog for customization
    - Contact sheet generation for the active section

    Sections:
    1. Light Layer
    2. Mask Layer
    3. Tech Layer
    4. Utility Layer
    5. Custom Layer (with customizable title)

    Node Creation Capabilities:
    - GradeAOV: For layers in the Light Layer section
    - Shuffle2: For layers in Mask, Tech, and Utility sections
    - Contribution: For layers in the Custom Layer section

    The interface is designed to adapt to user actions and provides visual feedback through
    color changes and tooltips.
    """

    channelChanged = Signal(str)

    def __init__(self, parent=None):
        super(LayerManagerUI, self).__init__(parent)
        self.last_selected_layer = None
        self.last_light_layer = None
        self.current_section = 0
        self.has_custom_layers = False
        self.channelChanged.connect(self.set_channel)
        self.section_keywords = load_section_keywords()
        self.mode = 'Lead'
        self.initUI()
        self.channel_list_widget.rowChanged.connect(self.update_viewer_channel)
        self.channel_list_widget.ctrlClicked.connect(self.handle_ctrl_click)
        self.channel_list_widget.shiftClicked.connect(self.handle_shift_click)
        self.channel_list_widget.keyPressed.connect(self.handle_keypress)
        self.setFocusPolicy(Qt.StrongFocus)

    def initUI(self):
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.rgba_button = QPushButton('RGBA')
        self.rgba_button.clicked.connect(lambda: self.set_channel('rgba'))
        self.rgba_button.setToolTip('Click to set the layer to RGBA')
        self.layout.addWidget(self.rgba_button)
        self.select_channel_label = QLabel('Select Layer')
        self.select_channel_label.setStyleSheet("QLabel { font-weight: bold; text-align: center; }")
        self.select_channel_label.setAlignment(Qt.AlignCenter)
        self.select_channel_label.setToolTip('This label shows the current section')
        self.layout.addWidget(self.select_channel_label)
        self.channel_list_widget = LayerSelector()
        self.channel_list_widget.setStyleSheet(
            "QListWidget::item { color: #c0c0c0; }"
            "QListWidget::item:selected { background: orange; color: black; }")
        self.channel_list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.channel_list_widget.itemClicked.connect(self.itemClicked)
        self.channel_list_widget.setToolTip('List of available layers')
        self.layout.addWidget(self.channel_list_widget)
        self.action_buttons_layout = QHBoxLayout()
        self.create_grade_button = QPushButton('Create Grade AOV')
        self.create_grade_button.clicked.connect(self.handle_action_button)
        self.add_layer_button = QPushButton('Add Layer AOV')
        self.add_layer_button.setToolTip('Add a layer to the current GradeAOV')
        self.add_layer_button.clicked.connect(self.handle_add_layer_button)
        self.action_buttons_layout.addWidget(self.create_grade_button)
        self.action_buttons_layout.addWidget(self.add_layer_button)
        self.layout.addLayout(self.action_buttons_layout)
        self.action_button = QPushButton('')
        self.action_button.clicked.connect(self.handle_action_button)
        self.layout.addWidget(self.action_button)
        if self.current_section == 0:
            self.layout.addLayout(self.action_buttons_layout)
        else:
            self.layout.addWidget(self.action_button)
        self.line2 = QFrame()
        self.line2.setFrameShape(QFrame.HLine)
        self.line2.setFrameShadow(QFrame.Sunken)
        self.line2.setToolTip('Second separator line')
        self.layout.addWidget(self.line2)
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.clicked.connect(lambda: self.channels())
        self.refresh_button.setToolTip('Refresh the list of layers')
        self.layout.addWidget(self.refresh_button)
        self.line1 = QFrame()
        self.line1.setFrameShape(QFrame.HLine)
        self.line1.setFrameShadow(QFrame.Sunken)
        self.line1.setToolTip('First separator line')
        self.layout.addWidget(self.line1)
        self.nav_layout = QHBoxLayout()
        self.prev_button = QPushButton('← Previous')
        self.next_button = QPushButton('Next →')
        self.nav_layout.addWidget(self.prev_button)
        self.nav_layout.addWidget(self.next_button)
        self.layout.addLayout(self.nav_layout)
        self.prev_button.clicked.connect(self.prev_section)
        self.next_button.clicked.connect(self.next_section)
        self.line3 = QFrame()
        self.line3.setFrameShape(QFrame.HLine)
        self.line3.setFrameShadow(QFrame.Sunken)
        self.line3.setToolTip('Third separator line')
        self.layout.addWidget(self.line3)
        self.contact_sheet_button = QPushButton('Create Contact Sheet')
        self.contact_sheet_button.clicked.connect(self.create_layer_contact_sheet)
        self.contact_sheet_button.setToolTip('Create a LayerContactSheet for the current section layers')
        self.layout.addWidget(self.contact_sheet_button)
        preferences_button = QPushButton("Preferences")
        preferences_button.clicked.connect(self.open_preferences)
        self.layout.addWidget(preferences_button)
        credits_line = QFrame()
        credits_line.setFrameShape(QFrame.HLine)
        credits_line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(credits_line)
        credits_label = QLabel(
            '<p align="center">'
            '<a href="https://github.com/Duckydav" style="text-decoration:none; color:#A2A1A1">'
            'Viewer<b><font color="#545454"> Layer</font></b> v01.2 &copy; 2024'
            '</a>'
            '</p>'
        )
        credits_label.setOpenExternalLinks(True)
        credits_label.setStyleSheet("font-size: 12px; color: #bbbbbb;")
        self.layout.addWidget(credits_label)
        self.setWindowTitle('Layer Manager')
        self.resize(260, 600)
        self.setWindowFlags(Qt.Tool)
        screen_geometry = QApplication.desktop().screenGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        self.channels()
        self.update_section_label()
        self.show()

    def open_preferences(self):
        dialog = PreferencesDialog(self)
        dialog.exec_()
        self.section_keywords = dialog.preferences
        self.update_section_label()

    def load_section_keywords(self):
        filepath = os.path.join(os.path.expanduser("~"), ".nuke", "layermanager_preferences.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as file:
                    return json.load(file)
            except Exception as e:
                print(f"Failed to load section keywords: {e}")
        return {
            "Light Layer": [],
            "Mask Layer": [],
            "Tech Layer": [],
            "Utility Layer": [],
            "custom Title": []
        }

    def get_current_user_name(self):
        return os.getenv('USER') or os.getenv('USERNAME') or 'unknown_user'

    def update_layer_selection(self, layer_name):
        self.last_selected_layer = layer_name
        if layer_name.startswith("CONT_specular_direct_"):
            self.last_light_layer = layer_name.replace("CONT_specular_direct_", "RGBA_")
        elif layer_name.startswith("CONT_specular_indirect_"):
            self.last_light_layer = layer_name.replace("CONT_specular_indirect_", "RGBA_")
        else:
            self.last_light_layer = None
        print(f"Layer selection updated: {self.last_selected_layer}, Parent RGBA Layer: {self.last_light_layer}")

    def create_Shuffle(self, item):
        try:
            group = nuke.thisGroup()
            if group is None:
                group = nuke.root()

            with group:
                last_selected_node = None
                if nuke.selectedNodes():
                    last_selected_node = nuke.selectedNodes()[-1]
                else:
                    viewer = nuke.activeViewer()
                    if viewer:
                        viewer_node = viewer.node()
                        input_index = viewer.activeInput()
                        if input_index is not None:
                            last_selected_node = viewer_node.input(input_index)

                if last_selected_node is None:
                    nuke.message("No relevant node found to place the Shuffle node next to.")
                    print("No relevant node found to place the Shuffle node next to.")
                    return

                # Create a shuffle node
                shuffle_node = nuke.createNode('Shuffle')

                # Place the Shuffle node next to the "watched" node
                shuffle_node.setXpos(int(last_selected_node.xpos() + last_selected_node.screenWidth() + 50))
                shuffle_node.setYpos(last_selected_node.ypos())

                # Configure the properties of the shuffle
                shuffle_node['in'].setValue('none')
                shuffle_node['in'].setValue(item.text())
                shuffle_node['label'].setValue(item.text())
                shuffle_node['in2'].setValue('rgba')

                print(f"Shuffle node created next to node: {last_selected_node.name()}")

        except Exception as e:
            nuke.message(f"Error creating Shuffle node: {str(e)}")
            print(f"Error creating Shuffle node: {str(e)}")

    def create_Shuffle2(self, item):
        try:
            group = nuke.thisGroup()
            if group is None:
                group = nuke.root()

            with group:
                if self.current_section in [0, 1, 2, 3, 4]:
                    last_selected_node = None
                    viewer = nuke.activeViewer()
                    if viewer:
                        viewer_node = viewer.node()
                        input_index = viewer.activeInput()
                        if input_index is not None:
                            last_selected_node = viewer_node.input(input_index)

                    if last_selected_node is None:
                        nuke.message("No relevant node found to place the Shuffle2 node next to.")
                        print("No relevant node found to place the Shuffle2 node next to.")
                        return

                    # Create a Shuffle 2 knot
                    shuffle2_node = nuke.createNode('Shuffle2')

                    # Obtain the visible central position of the Node Graph
                    current_center = nuke.center()
                    zoom_level = nuke.zoom()

                    # Adjust the coordinates so that they relate to the visible view
                    center_x = int(current_center[0])
                    center_y = int(current_center[1])

                    # Position the node in the visible center of the Node Graph
                    shuffle2_node.setXpos(center_x - shuffle2_node.screenWidth() // 2)
                    shuffle2_node.setYpos(center_y - shuffle2_node.screenHeight() // 2)

                    shuffle2_node['in1'].setValue(item.text())
                    shuffle2_node['label'].setValue(item.text())

                    # Get the channels available for this layer
                    all_channels = nuke.channels()
                    available_channels = [ch for ch in all_channels if ch.startswith(item.text())]

                    # Configure mappings according to the available channels
                    mappings = []
                    if item.text() == 'motion':
                        mappings = [(0, 'forward.u', 'rgba.red'), (0, 'forward.v', 'rgba.green'),
                                    (0, 'backward.u', 'rgba.blue'), (0, 'backward.v', 'rgba.alpha')]
                    elif item.text() == 'N':
                        mappings = [(0, 'N.X', 'rgba.red'), (0, 'N.Y', 'rgba.green'), (0, 'N.Z', 'rgba.blue'),
                                    (-1, 'black', 'rgba.alpha')]
                    elif item.text() == 'N_filter':
                        mappings = [(0, 'N_filter.X', 'rgba.red'), (0, 'N_filter.Y', 'rgba.green'),
                                    (0, 'N_filter.Z', 'rgba.blue'),
                                    (-1, 'black', 'rgba.alpha')]
                    elif item.text() == 'P':
                        mappings = [(0, 'P.X', 'rgba.red'), (0, 'P.Y', 'rgba.green'), (0, 'P.Z', 'rgba.blue'),
                                    (-1, 'black', 'rgba.alpha')]
                    elif item.text() == 'P_filter':
                        mappings = [(0, 'P_filter.X', 'rgba.red'), (0, 'P_filter.Y', 'rgba.green'),
                                    (0, 'P_filter.Z', 'rgba.blue'),
                                    (-1, 'black', 'rgba.alpha')]
                    elif item.text() == 'depth':
                        mappings = [(0, 'depth/home/dfrancois/private/.nuke/gizmos/GradePass_ref.gizmo.Z', 'rgba.red'), (-1, 'black', 'rgba.green'), (-1, 'black', 'rgba.blue'),
                                    (-1, 'black', 'rgba.alpha')]
                    elif item.text() == 'rfx_depth':
                        mappings = [(0, 'rfx_depth.Z', 'rgba.red'), (-1, 'black', 'rgba.green'),
                                    (-1, 'black', 'rgba.blue'),
                                    (-1, 'black', 'rgba.alpha')]
                    elif item.text() == 'other':
                        mappings = [(0, 'other.caustic', 'rgba.red'), (-1, 'other.glint', 'rgba.green'),
                                    (-1, 'other.rfx_depth', 'rgba.blue'),
                                    (-1, 'black', 'rgba.alpha')]
                    else:
                        # For other layers, map the RGBA channels generic
                        channel_map = {'red': 'red', 'green': 'green', 'blue': 'blue', 'alpha': 'alpha'}
                        for channel in ['red', 'green', 'blue', 'alpha']:
                            input_channel = f'{item.text()}.{channel}'
                            if input_channel in available_channels:
                                output_channel = f'rgba.{channel_map[channel]}'
                                mappings.append((0, input_channel, output_channel))

                        # Redirect the alpha channel to red
                        mappings.append((0, f'{item.text()}.red', 'rgba.alpha'))

                    if mappings:
                        shuffle2_node['mappings'].setValue(mappings)

                    print(f"Shuffle2 node created next to node: {last_selected_node.name()}")

        except Exception as e:
            nuke.message(f"Error creating Shuffle2 node: {str(e)}")
            print(f"Error creating Shuffle2 node: {str(e)}")

    def create_gradepass(self, item):
        try:
            # Put the channels on RGBA in the active viewer
            viewer = nuke.activeViewer()
            if viewer:
                viewerNode = viewer.node()
                if 'channels' in viewerNode.knobs():
                    viewerNode['channels'].setValue('rgba')
                    print("Viewer set back to RGBA channels")

            group = nuke.thisGroup() or nuke.root()

            with group:
                # Identify the last selected node or active entry of the viewer
                last_selected_node = None
                selected_nodes = [node for node in nuke.selectedNodes() if node.Class() != "Viewer"]
                if selected_nodes:
                    last_selected_node = selected_nodes[-1]
                elif viewer:
                    viewer_node = viewer.node()
                    input_index = viewer.activeInput()
                    if input_index is not None:
                        last_selected_node = viewer_node.input(input_index)

                if last_selected_node is None:
                    nuke.message("No relevant node found to place the GradeAOV node.")
                    return

                # ✅ Check if the last selected node is valid before positioning
                if last_selected_node is None:
                    nuke.message("Aucune sélection valide trouvée. Sélectionne un nœud avant d'ajouter un GradeAOV.")
                    return

                # Create the node `GradeAOV`
                node = nuke.createNode('gradepass', inpanel=False)

                # ✅ Check if the Gradeaov` node has been created before positioning it
                if node is None:
                    nuke.message("Erreur lors de la création du GradeAOV.")
                    return

                # ✅ Add a verification before defining the node position
                try:
                    node.setXpos(
                        int(last_selected_node.xpos() + last_selected_node.screenWidth() / 2 - node.screenWidth() / 2))
                    node.setYpos(int(last_selected_node.ypos() + 70))
                except Exception as e:
                    print(f"Erreur lors du positionnement du GradeAOV : {e}")
                    nuke.message(f"Erreur lors du positionnement du GradeAOV : {e}")

                # Configure the Knobs
                node["layers_options_add_layer_pyscript"].execute()
                node["layer_0_link"].setValue(item.text())

                # ✅ Open the properties window and display the Settings tab if possible
                try:
                    nuke.show(node)
                    tab_knobs = [knob for knob in node.knobs().values() if knob.Class() == "Tab_Knob"]
                    for tab in tab_knobs:
                        if "Settings" in tab.label():
                            node[tab.name()].setFlag(0x1000)
                            break
                except Exception as e:
                    print(f"Erreur lors de l'affichage du nœud : {e}")

                print(f"GradeAOV node created with layer '{item.text()}'.")

        except Exception as e:
            nuke.message(f"Error creating GradeAOV node: {str(e)}")
            print(f"Error creating GradeAOV node: {str(e)}")

    def create_contribution(self, item=None):
        try:
            # Display the memory buffer for debugging
            print(f"Using memory: Last selected layer is '{self.last_selected_layer}'")

            # Use the item if provided, otherwise fall back to the memory buffer
            contribution_layer = item.text() if item else self.last_selected_layer
            if not contribution_layer:
                nuke.message("No valid layer selected or in memory!")
                print("No valid layer selected or in memory!")
                return

            # Identify the parent RGBA layer
            if contribution_layer.startswith("CONT_specular_direct_"):
                light_layer = contribution_layer.replace("CONT_specular_direct_", "RGBA_")
            elif contribution_layer.startswith("CONT_specular_indirect_"):
                light_layer = contribution_layer.replace("CONT_specular_indirect_", "RGBA_")
            else:
                nuke.message(f"Unknown contribution layer format: {contribution_layer}")
                print(f"Unknown contribution layer format: {contribution_layer}")
                return

            group = nuke.thisGroup() or nuke.root()

            with group:
                last_selected_node = None
                selected_nodes = [node for node in nuke.selectedNodes() if node.Class() != "Viewer"]
                if selected_nodes:
                    last_selected_node = selected_nodes[-1]
                else:
                    viewer = nuke.activeViewer()
                    if viewer:
                        viewer_node = viewer.node()
                        input_index = viewer.activeInput()
                        if input_index is not None:
                            last_selected_node = viewer_node.input(input_index)

                if last_selected_node is None:
                    nuke.message("No relevant node found to place the Contribution node.")
                    print("No relevant node found to place the Contribution node.")
                    return

                # Create the Contribution node
                cont_node = nuke.createNode('contribution', inpanel=False)

                # Position the node
                cont_node.setXpos(
                    int(last_selected_node.xpos() + last_selected_node.screenWidth() / 2 - cont_node.screenWidth() / 2))
                cont_node.setYpos(int(last_selected_node.ypos() + 70))

                # Configure the knobs
                cont_node['layer_layer_light_choice'].setValue(light_layer)
                cont_node['layer_layer_contribution_choice'].setValue(contribution_layer)

                # Add a label
                label_expression = '[regsub -all "CONT_" [value layer_layer_contribution_choice] ""]'
                cont_node['label'].setValue(label_expression)

                # Open the properties window
                nuke.show(cont_node)
                print(
                    f"Contribution node created with light layer '{light_layer}' and contribution layer '{contribution_layer}'.")

        except Exception as e:
            nuke.message(f"Error creating Contribution node: {str(e)}")
            print(f"Error creating Contribution node: {str(e)}")

    def Ctrl_Click(self, item):
        if self.current_section in [0]:
            self.create_gradepass(item)
        elif self.current_section in [1, 2, 3]:
            self.create_Shuffle2(item)
        elif self.current_section in [4]:
            self.create_contribution(item)

    def handle_action_button(self):
        selected_item = self.channel_list_widget.currentItem()
        if selected_item:
            if self.current_section == 0:
                self.create_gradepass(selected_item)
            elif self.current_section in [1, 2, 3]:
                self.create_Shuffle2(selected_item)
            elif self.current_section == 4:
                self.create_contribution(selected_item)

    def handle_ctrl_click(self, item):
        """Create a shuffle2 with Ctrl + Click on a Channel Layer."""
        print(f"Ctrl + Click detected on layer: {item.text()}")
        self.create_Shuffle2(item)

    def handle_shift_click(self, item):
        """
        Action activated by Shift+Click.
        - Section 0 : Create GradeAOV.
        - Section 4 : Create contribution.
        """
        try:
            if self.current_section == 0:
                print(f"Shift+Click detected in Light Layer on layer: {item.text()}")
                self.create_gradepass(item)
            elif self.current_section == 4:
                print(f"Shift+Click detected in custom Layer on layer: {item.text()}")
                self.create_contribution(item)
            else:
                print("Shift+Click is only enabled in Light Layer (Section 0) and custom Layer (Section 4).")
        except Exception as e:
            nuke.message(f"Error handling Shift+Click: {str(e)}")
            print(f"Error handling Shift+Click: {str(e)}")

    def handle_shift_ctrl_click(self, item):
        """Action activated by Shift+Ctrl+Click to add a layer to the selected GradeAOV."""
        if self.current_section == 0:
            print(f"Shift+Ctrl+Click detected on layer: {item.text()}")
            self.add_layer_to_gradepass(item)
        else:
            print("Shift+Ctrl+Click is only enabled in Light Layer (Section 0).")

    def handle_keypress(self, key):
        print(f"LayerManagerUI received key: {key}")
        selected_item = self.channel_list_widget.currentItem()

        if key == Qt.Key_G:
            if self.current_section == 0:
                print("Shortcut: G - Create Grade AOV")
                if selected_item:
                    self.create_gradepass(selected_item)
            elif self.current_section in [1, 2, 3]:
                print("Shortcut: G - Create Shuffle2")
                if selected_item:
                    self.create_Shuffle2(selected_item)
            elif self.current_section == 4:
                print("Shortcut: G - Create contribution")
                if selected_item:
                    self.create_contribution(selected_item)

    def handle_add_layer_button(self):
        if self.current_section in [1, 2, 3]:
            self.add_layer_button.setEnabled(False)
            return
        else:
            self.add_layer_button.setEnabled(True)

        selected_item = self.channel_list_widget.currentItem()
        if selected_item:
            # Check and recover the Gradeaov node currently selected
            gradepass_node = None
            for node in nuke.selectedNodes():
                if node.Class() == 'Group' and node.name().startswith('GradePass'):
                    gradepass_node = node
                    break

            if gradepass_node is None:
                nuke.message('No GradeAOV node selected.')
                return

            # Add a layer using the python script defined in the node
            gradepass_node["layers_options_add_layer_pyscript"].execute()

            # Recover the layers counter and adjust the index for the new layer
            layer_count = int(gradepass_node["layer_count"].value()) - 1
            knob_name = "layer_{}_link".format(layer_count)

            # Update the value of the Knob with the name of the selected layer
            gradepass_node[knob_name].setValue(selected_item.text())

            # Update the appearance of the elements of the list
            self.channel_list_widget.setStyleSheet(
                "QListWidget::item { color: #c0c0c0; }"
                "QListWidget::item:selected { background: orange; color: black; }"
            )
            selected_item.setBackground(QColor('#01859F'))
            selected_item.setForeground(QColor('black'))

            for i in range(self.channel_list_widget.count()):
                self.channel_list_widget.item(i).setBackground(QColor('transparent'))
                self.channel_list_widget.item(i).setForeground(QColor('black'))

    def handle_action_button(self):
        selected_item = self.channel_list_widget.currentItem()
        print(f"Action button clicked. Selected section: {self.current_section}, Selected item: {selected_item}")
        if selected_item:
            if self.current_section == 0:
                self.create_gradepass(selected_item)
            elif self.current_section in [1, 2, 3]:
                self.create_Shuffle2(selected_item)
            elif self.current_section == 4:
                self.create_contribution(selected_item)

    def create_layer_contact_sheet(self):
        try:
            group = nuke.thisGroup()
            if group is None:
                group = nuke.root()

            with group:
                layers = []
                section_name = self.getSectionText()

                for index in range(self.channel_list_widget.count()):
                    item = self.channel_list_widget.item(index)
                    if item and item.text() and item.text() != "!!! Layer Empty !!!":
                        layers.append(item.text())

                if not layers:
                    nuke.message('No valid layers found to create LayerContactSheet.')
                    return

                # Get the last selection
                selected_nodes = nuke.selectedNodes()
                if not selected_nodes:
                    nuke.message('No nodes selected.')
                    return
                last_selected_node = selected_nodes[-1]

                # Create a group to encapsulate all nodes
                group_name = "{} ContactSheet".format(section_name)
                group_node = nuke.createNode('Group', inpanel=False)
                group_node.setName(group_name)
                group_node['tile_color'].setValue(4278190335)

               # Enter the group to create the nodes inside
                group_node.begin()

                # Create the Input node
                input_node = nuke.createNode('Input', inpanel=False)
                input_dot = nuke.createNode('Dot', inpanel=False)
                input_dot.setInput(0, input_node)
                input_dot.setYpos(input_dot.ypos() - 50)

                shuffle_nodes = []
                text_nodes = []
                crop_nodes = []
                grid_nodes = []

                xpos_start = input_dot.xpos() - (
                        80 * len(layers) // 2)

                for i, layer in enumerate(layers):
                    shuffle_node = nuke.createNode('Shuffle', inpanel=False)
                    shuffle_node['in'].setValue(layer)
                    shuffle_node['label'].setValue(layer)
                    shuffle_node.setInput(0, input_dot)

                    xpos = xpos_start + (i * 80)
                    shuffle_node.setXpos(xpos)
                    shuffle_node.setYpos(input_dot.ypos() + 100)
                    shuffle_nodes.append(shuffle_node)

                    crop_node = nuke.createNode('Crop', inpanel=False)
                    crop_node['box'].setValue(
                        [-14, -70, 2012, 1090])
                    crop_node['reformat'].setValue(True)
                    crop_node.setInput(0, shuffle_node)

                    crop_node.setXpos(xpos)
                    crop_node.setYpos(shuffle_node.ypos() + 50)
                    crop_nodes.append(crop_node)

                    grid_node = nuke.createNode('Grid', inpanel=False)
                    grid_node['number'].setValue(1)
                    grid_node['size'].setValue(4)
                    grid_node.setInput(0, crop_node)

                    grid_node.setXpos(xpos)
                    grid_node.setYpos(crop_node.ypos() + 100)
                    grid_nodes.append(grid_node)

                    text_node = nuke.createNode('Text', inpanel=False)
                    text_node['message'].setValue(layer)
                    text_node['box'].setValue([0, 0, 1998, 1080])
                    text_node['xjustify'].setValue('center')
                    text_node['yjustify'].setValue('bottom')
                    text_node.setInput(0, grid_node)

                    text_node.setXpos(xpos)
                    text_node.setYpos(grid_node.ypos() + 100)
                    text_nodes.append(text_node)

               # Calculate the values of Rows and Columns
                num_layers = len(layers)
                rows = int(math.floor(math.sqrt(num_layers)))
                columns = int(math.ceil(num_layers / rows))

                contact_sheet_node = nuke.createNode('ContactSheet', inpanel=False)
                contact_sheet_node['width'].setValue(1998)
                contact_sheet_node['height'].setValue(1080)
                contact_sheet_node['rows'].setValue(rows)
                contact_sheet_node['columns'].setValue(columns)
                contact_sheet_node['center'].setValue(True)
                contact_sheet_node['roworder'].setValue('TopBottom')
                contact_sheet_node['gap'].setValue(8)

                for i, text_node in enumerate(text_nodes):
                    contact_sheet_node.setInput(i, text_node)

                contact_sheet_node.setXpos(input_dot.xpos())
                contact_sheet_node.setYpos(
                    text_nodes[0].ypos() + 200)

                # Create the output node and connect it to the contactsheet
                output_node = nuke.createNode('Output', inpanel=False)
                output_node.setInput(0, contact_sheet_node)

                # Exit the group
                group_node.end()

                # Connect the output of the last selection to the input node of the group
                group_node.setInput(0, last_selected_node)

                # Select and activate the Viewer
                viewer_nodes = nuke.allNodes('Viewer')
                if viewer_nodes:
                    viewer_node = viewer_nodes[0]
                    viewer_node.setInput(0, group_node)

                nuke.message('LayerContactSheet created with layers: {}'.format(', '.join(layers)))

                # Reset to RGBA
                self.set_channel('rgba')

        except Exception as e:
            nuke.message(f"Error creating LayerContactSheet: {str(e)}")
            print(f"Error creating LayerContactSheet: {str(e)}")

    def add_layer_to_gradepass(self, item):
        """Centralized logic to add a layer to the selected GradeAOV."""
         # Verify and recover the currently selected GradeAOV node
        gradepass_node = None
        for node in nuke.selectedNodes():
            if node.Class() == 'Group' and node.name().startswith('gradepass'):
                gradepass_node = node
                break

        if gradepass_node is None:
            nuke.message('No GradeAOV node selected.')
            print('No GradeAOV node selected.')
            return

        try:
            # Add a layer using the Python script defined in the node
            gradepass_node["layers_options_add_layer_pyscript"].execute()

            # Retrieve the layer counter and adjust the index for the new layer
            layer_count = int(gradepass_node["layer_count"].value()) - 1
            knob_name = f"layer_{layer_count}_link"

            # Update the knob value with the name of the selected layer
            gradepass_node[knob_name].setValue(item.text())

            # Update the colors to indicate that the layer has been added
            item.setBackground(QColor('#01859F'))
            item.setForeground(QColor('black'))

            print(f"Layer '{item.text()}' added to GradeAOV.")
        except Exception as e:
            nuke.message(f"Error adding layer to GradeAOV: {str(e)}")
            print(f"Error adding layer to GradeAOV: {str(e)}")

    def get_selected_channel(self):
        """Retrieves the layer currently selected from the list."""
        selected_item = self.channel_list_widget.currentItem()
        if selected_item:
            return selected_item.text()
        else:
            return None

    def update_section_label(self):
        try:
            self.action_button.clicked.disconnect()
        except Exception as e:
            print(f"Error disconnecting previous actions: {e}")

        # Checks the custom title for the section "Custom Layer"
        custom_title = self.section_keywords.get("custom Title", "custom Layer")
        if not isinstance(custom_title, str):
            custom_title = "custom Layer"

        # HTML for the style of the titles
        title_style = """
            <p align="center" style="font-size: 16px; font-weight: bold; color: #FCB132; margin: 0;">
                {title} <span style="color: #FFFFFF;">Layer</span>
            </p>
        """

        if self.current_section == 0:
            self.select_channel_label.setText(title_style.format(title="Light"))

            # Enable both buttons to Light Layer
            self.create_grade_button.setVisible(True)
            self.add_layer_button.setVisible(True)
            self.action_button.setVisible(False)

            self.prev_button.setText('← prev.')
            self.next_button.setText('next →')

        else:  # Other sections
            self.select_channel_label.setText(title_style.format(
                title=("Mask" if self.current_section == 1 else
                       "Tech" if self.current_section == 2 else
                       "Utility" if self.current_section == 3 else custom_title)
            ))

            # Activate the single button and configure its text
            self.action_button.setVisible(True)
            self.create_grade_button.setVisible(False)
            self.add_layer_button.setVisible(False)

            if self.current_section == 1:  # Mask Layer
                self.action_button.setText('Create Shuffle')
                self.action_button.clicked.connect(self.handle_action_button)
                self.action_button.setToolTip('Create Shuffle for selected layer\nor Ctrl+Click on selected layer')
            elif self.current_section == 2:  # Tech Layer
                self.action_button.setText('Create Shuffle')
                self.action_button.clicked.connect(self.handle_action_button)
                self.action_button.setToolTip('Create Shuffle for selected layer\nor Ctrl+Click on selected layer')
            elif self.current_section == 3:  # Utility Layer
                self.action_button.setText('Create Shuffle')
                self.action_button.clicked.connect(self.handle_action_button)
                self.action_button.setToolTip('Create Shuffle for selected layer\nor Ctrl+Click on selected layer')
            elif self.current_section == 4:  # Custom Layer
                # Use the default custom title
                custom_title = self.section_keywords.get("custom Title", "").strip()
                if not custom_title:
                    custom_title = "custom"
                self.select_channel_label.setText(
                    f'<p align="center" style="font-size: 16px; font-weight: bold; color: #FCB132; margin: 0;">'
                    f'{custom_title} <span style="color: #FFFFFF;">Layer</span>'
                    f'</p>'
                )
                self.action_button.setText('Create Contribution Grade')
                self.action_button.clicked.connect(self.handle_action_button)
                self.action_button.setToolTip(
                    'Create Contribution Grade for selected layer\nor Ctrl+Click on selected layer')

            self.prev_button.setText('← prev.')
            self.next_button.setText('next →')

        # Refresh the displayed layers
        self.channels()


    def channels(self):
        self.channel_list_widget.clear()
        self.active_viewer = nuke.activeViewer().node()
        viewer = self.active_viewer.input(nuke.activeViewer().activeInput())
        all_layers = list(set([layer.split('.')[0] for layer in viewer.channels()]))

        filtered_layers = self.get_filtered_layers(all_layers)
        if not filtered_layers:
            filtered_layers = []

        filtered_layers.sort()



        for layer in filtered_layers:
            item = QListWidgetItem(layer)
            self.channel_list_widget.addItem(item)

        if not filtered_layers:
            for _ in range(4):
                empty_item = QListWidgetItem("")
                self.channel_list_widget.addItem(empty_item)

            empty_item = QListWidgetItem("!!! Layer Empty !!!")
            empty_item.setTextAlignment(Qt.AlignCenter)
            font = empty_item.font()
            font.setBold(True)
            empty_item.setFont(font)
            self.channel_list_widget.addItem(empty_item)

            # Keep the button on even if the list is empty
            self.action_button.setEnabled(True)
            self.channel_list_widget.is_empty_layer_present = True
        else:
            self.action_button.setEnabled(True)
            self.channel_list_widget.is_empty_layer_present = False

    def get_filtered_layers(self, all_layers):
        """Keep the button on even if the list is empty"""
        keywords = self.section_keywords
        exclusion_keywords = keywords.get("Exclusion Keywords", [])

        # Exclude layers containing exclusion keywords
        filtered_layers = [layer for layer in all_layers if not any(kw in layer for kw in exclusion_keywords)]

        # Function to get the main prefix of a layer (up to the next '_' or '-')
        def get_prefix(layer):
            if '_' in layer:
                return layer.split('_')[0]
            elif '-' in layer:
                return layer.split('-')[0]
            else:
                return layer

        # Function to check if a layer exactly matches a keyword or prefix
        def matches_keyword(layer, section_keywords):
            prefix = get_prefix(layer)
            for kw in section_keywords:
                if len(kw) == 1:
                    if layer == kw or prefix == kw:
                        return True
                elif len(kw) > 1:
                    if prefix == kw or kw in layer:
                        return True
            return False

        # Prioritize keywords "custom Layer"
        custom_layers = [layer for layer in filtered_layers if matches_keyword(layer, keywords["custom Layer"])]
        filtered_layers = [layer for layer in filtered_layers if layer not in custom_layers]

        # Filtering for each remaining section
        light_layers = [layer for layer in filtered_layers if matches_keyword(layer, keywords["Light Layer"])]
        mask_layers = [layer for layer in filtered_layers if matches_keyword(layer, keywords["Mask Layer"])]
        tech_layers = [layer for layer in filtered_layers if matches_keyword(layer, keywords["Tech Layer"])]
        utils_layers = [layer for layer in filtered_layers if matches_keyword(layer, keywords["Utility Layer"])]

        # Identify unclassified layers and avoid duplicates
        classified_layers = set(light_layers + mask_layers + tech_layers + utils_layers + custom_layers)
        unclassified_layers = [layer for layer in filtered_layers if layer not in classified_layers]

        # Add unclassified layers to "Tech Layer"
        tech_layers += unclassified_layers

        # Remove duplicates in each section
        light_layers = list(set(light_layers))
        mask_layers = list(set(mask_layers))
        tech_layers = list(set(tech_layers))
        utils_layers = list(set(utils_layers))
        custom_layers = list(set(custom_layers))

        if self.current_section == 0:
            return sorted(light_layers)
        elif self.current_section == 1:
            return sorted(mask_layers)
        elif self.current_section == 2:
            return sorted(tech_layers)
        elif self.current_section == 3:
            return sorted(utils_layers)
        elif self.current_section == 4:
            return sorted(custom_layers)
        return []

    def prev_section(self):
        if self.mode == 'Artist':
            if self.current_section == 0:
                self.current_section = 4
            elif self.current_section == 4:
                self.current_section = 1
            else:
                self.current_section -= 1
        else:
            self.current_section = (self.current_section - 1) % 5
        self.channels()
        self.update_section_label()

    def next_section(self):
        if self.mode == 'Artist':
            if self.current_section == 1:
                self.current_section = 4
            elif self.current_section == 4:
                self.current_section = 0
            else:
                self.current_section = (self.current_section + 1) % 4
        else:
            self.current_section = (self.current_section + 1) % 5
        self.channels()
        self.update_section_label()

    def print_current_section_layers(self):
        self.active_viewer = nuke.activeViewer().node()
        viewer = self.active_viewer.input(nuke.activeViewer().activeInput())
        all_layers = list(set([layer.split('.')[0] for layer in viewer.channels()]))

        filtered_layers = self.get_filtered_layers(all_layers)
        print(f"Layers in section {self.current_section}: {filtered_layers}")

    def getSectionText(self):
        if self.current_section == 0:
            return "Light Layer"
        elif self.current_section == 1:
            return "Mask Layer"
        elif self.current_section == 2:
            return "Tech Layer"
        elif self.current_section == 3:
            return "Utility Layer"
        elif self.current_section == 4:
            # Load the custom preference title
            custom_title = self.section_keywords.get("custom Title", "custom Layer")
            return custom_title if custom_title.strip() else "custom Layer"
        return ""

    def resetLabel(self):
        originalText = "Light Layer" if self.current_section == 0 else "Mask Layer" if self.current_section == 1 else "Tech Layer" if self.current_section == 2 else "Utility Layer"
        self.select_channel_label.setStyleSheet(
            "QLabel { background-color: none; font-weight: bold; text-align: center; }")
        self.select_channel_label.setText(originalText)


    def keyPressEvent(self, event):
        print(f"LayerManagerUI captured key: {event.key()}")
        current_row = self.channel_list_widget.currentRow()
        selected_item = self.channel_list_widget.currentItem()

        # Shortcut section 0 : G = create_GradeAOV
        if event.key() == Qt.Key_G and self.current_section == 0:
            print("Shortcut: G - Create Grade AOV")
            if selected_item:
                self.create_gradepass(selected_item)

        # Shortcut  section 4 : G = create_contribution
        elif event.key() == Qt.Key_G and self.current_section == 4:
            print("Shortcut: G - Create contribution")
            if selected_item:
                self.create_contribution(selected_item)

        # Navigation or other shortcuts
        elif event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Up:
            new_row = max(0, current_row - 1)
            self.channel_list_widget.setCurrentRow(new_row)
            self.update_viewer_channel(new_row)
        elif event.key() == Qt.Key_Down:
            new_row = min(self.channel_list_widget.count() - 1, current_row + 1)
            self.channel_list_widget.setCurrentRow(new_row)
            self.update_viewer_channel(new_row)
        elif event.key() == Qt.Key_Left:
            self.prev_section()
        elif event.key() == Qt.Key_Right:
            self.next_section()
        else:
            super(LayerManagerUI, self).keyPressEvent(event)

    def update_viewer_channel(self, row):
        if row != -1:
            item = self.channel_list_widget.item(row)
            if item:
                self.last_selected_layer = item.text()
                print(f"Memory updated: Last selected layer is '{self.last_selected_layer}'")
                nuke.executeInMainThread(self.set_channel, item.text())
            else:
                print("No item found for the current row.")
        else:
            print("Invalid row index.")

    def set_channel(self, channel):
        try:
            print(f"Setting layer to: {channel}")
            viewer = nuke.activeViewer()
            if viewer:
                viewer_node = viewer.node()
                current_channel = viewer_node['channels'].value()
                if current_channel != channel:
                    viewer_node['channels'].setValue(channel)
                    print(f"Viewer updated to channel: {channel}")
                else:
                    print(f"Viewer already set to channel: {channel}")
            else:
                print("No active viewer found.")
        except Exception as e:
            print(f"Error setting channel: {e}")

    def itemClicked(self, item):
        layer = item.text()
        self.set_channel(layer)

    def closeEvent(self, event):
        if nuke.exists('root'):
            viewer = nuke.activeViewer()
            if viewer:
                viewerNode = viewer.node()
                viewerNode['channels'].setValue('rgba')
                print("Viewer set back to rgba")
        event.accept()


def load_authorized_users(filepath):
    try:
        with open(filepath, 'r') as file:
            data = json.load(file)
            return data.get('authorized_users', [])
    except Exception as e:
        nuke.message(f"Error loading authorized users: {e}")
        print(f"Error loading authorized users: {e}")
        return []

def load_section_keywords():
    filepath = os.path.join(os.path.expanduser("~"), ".nuke", "layermanager_preferences.json")
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)

                # Check that "Custom Title" is a channel
                if "custom Title" in data and not isinstance(data["custom Title"], str):
                    data["custom Title"] = "custom"

                return data
        except Exception as e:
            print(f"Failed to load section keywords: {e}")
    return {
        "Light Layer": [],
        "Mask Layer": [],
        "Tech Layer": [],
        "Utility Layer": [],
        "custom Layer": [],
        "custom Title": "custom"
    }

def run():
    if nuke.allNodes('Viewer'):
        if nuke.activeViewer():
            global channel_list_window
            channel_list_window = LayerManagerUI()
        else:
            nuke.message('No active viewer connected to node.')
    else:
        nuke.message('No viewer found in script.')