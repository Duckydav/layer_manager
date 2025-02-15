# Layer Manager v1.3

**Description:** This tool provides a user-friendly interface for quickly visualizing Viewer Layer Channels with a single click, and organizes layers into sections like \
**Light, Mask, Utilities, Technic, or Custom layers.**\
&#x20;It also enables the addition a GradeAOV on Light layer, contribution or shuffle on selected layer channel, and allows navigating layers or sections using keyboard arrows for quick visualization. The tool also includes the **GradeAOV** node for Light Layers, the **Contribution** Grade node for Contribution Layers, and the **Shuffle Auto** tool to visualize their connections in shuffle node.

### Features

- Efficiently navigate through available layers
- Customizable sections and preferences for better organization
- Easily create **GradeAOV, Shuffle**, and **Contribution Grade** nodes
- Create Contact sheet by section



### Files to Include

1. **layermanager.py**: Main code file.

2. **README.md**: Detailed instructions and overview.

3. **menu.py**: Integration with Nuke.

4. **LICENSE**: : License file (Apache License 2.0).

5. **gradeaov.py**: Node Group  for Grade AOV. This node is used for grading Light AOV layers and allows adding multiple layers to the same GradeAOV, up to 11 layers.

6. **shuffle.py**: Tools for Shuffle & Shuffle2.

7. **contribution.py**: Node Group for Contribution for grading Contribution layers from AOV Layers.

8. **layermanager_preferences.json**: Configuration file to set layer preferences. This file allows configuring the tool and defining channel layer sections such as Light, Mask, Utility, Technic, and Custom..

### Installation Instructions

Before starting, place the file `layermanager_preferences.json` at the root of `.nuke/`. This file configures tool preferences and section layers.


1. Place the following files in the `.nuke/plugins` directory:

   - `layermanager.py`
   - `gradeaov.py`
   - `shuffle.py`
   - `contribution.py`

2. Place the following files in the `.nuke/gizmos` directory:

   - `gradeaov.gizmo`
   - `contribution.gizmo`

3. Update `menu.py` to include:

```python
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
import gradeaov
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
nuke.addOnCreate(gradeaov.knobChanged, nodeClass="gradeaov")
```

4. Restart Nuke.

### Usage

- **Open the interface:** Press `` ` `` (key between ESC and TAB).
- **Layer navigation:** Use ↑ & ↓ to change layer and ← & → to change section.
- **Create GradeAOV:** Select layer and press `G`.
- **Add Layer AOV:** With the Grade AOV node, you can add multiple Light Layers in the same node, up to 11 layers.
- **Create Contribution Grade:** Select layer and press `Shift+G`.
- **Run Shuffle Auto:** Press V on shuffle or shuffle2 node to see input and output connections.

### Contribution

We welcome contributions! See the [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### License

This project is licensed under the GNU GPL v3 License. See the [LICENSE](LICENSE) file for details.

##

