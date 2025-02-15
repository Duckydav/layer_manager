# Layer Manager v1.3

**Description:** This tool provides a user-friendly interface for quickly visualizing Viewer Layer Channels with a single click. It also enables the addition of a GradeAOV layer with a second click when selecting a Light Layer.

### Features

- Efficiently navigate through available layers
- Easily create GradeAOV, Shuffle, and Contribution nodes
- Customizable sections and preferences for better organization

### Files to Include

1. **layermanager.py**: Main code file.
2. **README.md**: Detailed instructions and overview.
3. **CHANGELOG.md**: Version history.
4. **menu.py**: Integration with Nuke.
5. **LICENSE**: License file (if already present).
6. **CONTRIBUTING.md**: Guidelines for contributors.
7. **gradepass.py**: Python file for GradePass.
8. **shuffle.py**: Python file for Shuffle Auto.
9. **contribution.py**: Python file for Contribution node.

### Installation Instructions

1. Place the following files in the `.nuke/plugins` directory:
    - `layermanager.py`
    - `gradepass.py`
    - `shuffle.py`
    - `contribution.py`

2. Place the following files in the `.nuke/gizmos` directory:
    - `gradepass.gizmo`
    - `contribution.gizmo`

3. Update `menu.py` to include:
    ```python
    import nuke
    import layermanager
    import shuffle

    # Création du menu principal
    dd_tools_menu = nuke.menu('Nuke').addMenu('DD Tools')
    # Sous-menu LayerAOV Tools
    layeraov_menu = dd_tools_menu.addMenu('Layer Tools')
    layeraov_menu.addCommand('Layer Manager', 'layermanager.run()', '`')
    layeraov_menu.addCommand('Shuffle Auto', 'shuffle.run()', 'V')
    ```

4. Restart Nuke.

### Usage

- **Open the interface:** Press `` ` `` (key between ESC and TAB).
- **Layer navigation:** Use arrow keys.
- **Create GradeAOV:** Select layer and press `G`.
- **Create Contribution:** Select layer and press `Shift+G`.
- **Run Shuffle Auto:** Press `V`.

### Contribution

We welcome contributions! See the [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## README.md Content

# Layer Manager

**Layer Manager** is a Python tool for Nuke to simplify layer management.

## Features

- Visualize Viewer Layer Channels.
- One-click GradeAOV creation.
- Shuffle and Contribution nodes support.
- Customizable interface with section-specific preferences.

## Installation

Follow the instructions in the main documentation to set up the tool.

## Usage

Launch with `` ` `` (touche entre ESC et TAB) and navigate layers with arrow keys.

## Contribution

See [CONTRIBUTING.md](CONTRIBUTING.md) for participation guidelines.

## License

Licensed under the MIT License. See [LICENSE](LICENSE) for more information.")]}

