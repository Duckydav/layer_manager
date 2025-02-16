import os
import sys
import nuke

# Path definition
nuke_path = os.path.expanduser('~/.nuke')
plugins_path = os.path.join(nuke_path, 'plugins')
gizmos_path = os.path.join(nuke_path, 'gizmos')

# Add the gizmos folder
nuke.pluginAddPath(gizmos_path)

# Add paths to sys.path
for path in [nuke_path, plugins_path]:
    if path not in sys.path:
        sys.path.append(path)

import layermanager
import shuffle
import gradepass
import contribution

# Create the main menu
dd_tools_menu = nuke.menu('Nuke').addMenu('DD Tools')

# Submenu LayerAOV Tools
layeraov_menu = dd_tools_menu.addMenu('Layer Tools')
layeraov_menu.addCommand('Layer Manager', 'layermanager.run()', '`')
layeraov_menu.addCommand('Shuffle Auto', 'shuffle.run()', 'V')

# Register contributions if available
if hasattr(contribution, 'register_contribution'):
    contribution.register_contribution()

# Add Nuke callbacks
def register_callbacks():
    for node in nuke.allNodes("contribution"):
        node.knobChanged = contribution.knobChanged

nuke.addOnScriptLoad(register_callbacks)
nuke.addOnCreate(contribution.knobChanged, nodeClass="contribution")
nuke.addOnCreate(gradepass.knobChanged, nodeClass="gradepass")