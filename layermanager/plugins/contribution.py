#------------------------------------------------------------------------------#
#-------------------------------------------------------------------- HEADER --#

"""
:synopsis:
    Callback and helper functions for the contribution node.
"""

#------------------------------------------------------------------------------#
#------------------------------------------------------------------- IMPORTS --#

import nuke
import os
import json

#------------------------------------------------------------------------------#
#----------------------------------------------------------------- FUNCTIONS --#

def load_viewerpass_preferences():
    """Charge les préférences de Viewer Pass depuis le fichier JSON dans ~/.nuke."""
    preferences_path = os.path.join(os.path.expanduser("~"), ".nuke", "viewerpass_preferences.json")

    if not os.path.exists(preferences_path):
        print(f"⚠️ Le fichier {preferences_path} n'existe pas.")
        return {}

    try:
        with open(preferences_path, "r") as file:
            data = json.load(file)
            return data
    except Exception as e:
        print(f"⚠️ Erreur lors du chargement de {preferences_path}: {e}")
        return {}


# Charger les préférences dès le début du script
viewerpass_preferences = load_viewerpass_preferences()


def get_layers(node, category="Light Pass"):
    """Récupère les layers d'un nœud, optionnellement filtrés selon les préférences JSON."""
    channels = node.channels()
    layers = list(set([c.split('.')[0] for c in channels]))  # Extraire les layers

    # Charger la valeur de filtre depuis le JSON
    filter_values = viewerpass_preferences.get(category, [])

    if filter_values:
        layers = [layer for layer in layers if any(layer.startswith(f) for f in filter_values)]

    layers.sort()
    return layers


#------------------------------------------------------------------------------#
#----------------------------------------------------------------- CALLBACKS --#

def knobChanged():
    print("knobChanged triggered")

    n = nuke.thisNode()
    k = nuke.thisKnob()

    if k is None:
        print("knobChanged appelé sans knob valide !")
        return

    print(f"Knob: {k.name()}, Value: {k.value()}")

    if k.name() == "inputChange":
        input_node = n.input(0)
        if input_node:
            light_layers = get_layers(input_node, category="Light Pass")

            print(f"Light layers found: {light_layers}")
            n["layer_layer_light_choice"].setValues(light_layers)

            light_shuffle_node = n.node("light_shuffle")
            if light_shuffle_node:
                light_shuffle_node["in1"].setValue(n["layer_layer_light_choice"].value())

            populate_contribution(n, input_node)

    if k.name() == "layer_layer_light_choice":
        input_node = n.input(0)  # Vérifie que le nœud d'entrée est bien défini
        if input_node:
            populate_contribution(n, input_node)

        light_shuffle_node = n.node("light_shuffle")
        if light_shuffle_node:
            light_shuffle_node["in1"].setValue(n["layer_layer_light_choice"].value())

    if k.name() == "layer_layer_contribution_choice":
        contribution_node = n.node("contribution_shuffle")
        if contribution_node:
            contribution_node["in1"].setValue(n["layer_layer_contribution_choice"].value())



#------------------------------------------------------------------------------#
#----------------------------------------------------------------- FUNCTIONS --#

def populate_contribution(node, input_node):
    if input_node is None:
        print("⚠️ populate_contribution appelé sans input_node valide")
        return

    contribution_shuffle_node = node.node("contribution_shuffle")
    contribution_in_node = node.node("contribution_shuffle_in")

    light_choice = node["layer_layer_light_choice"].value()
    contribution_layers = get_layers(input_node, category="Contribution Pass")

    # Filtrer les layers correspondant à la sélection de light_choice
    filtered_contribution_layers = [layer for layer in contribution_layers if light_choice.replace("RGBA_", "") in layer]

    if not filtered_contribution_layers:
        print("⚠️ Aucun layer contribution trouvé")
        return

    # Met à jour le Pulldown Choice sans inclure "none"
    node["layer_layer_contribution_choice"].setValues(filtered_contribution_layers)

    # Sélectionne automatiquement le premier layer contribution
    default_contribution = filtered_contribution_layers[0]
    node["layer_layer_contribution_choice"].setValue(default_contribution)
    print(f"Default contribution selected: {default_contribution}")

    # Mise à jour du Shuffle avec le layer par défaut
    if contribution_shuffle_node:
        contribution_shuffle_node["in1"].setValue(default_contribution)
        contribution_shuffle_node["mappings"].setValue([
            (f"{default_contribution}.red", "rgba.red"),
            (f"{default_contribution}.green", "rgba.green"),
            (f"{default_contribution}.blue", "rgba.blue")
        ])

    refresh_ui("layer_layer_contribution_choice")

def refresh_ui(knob_name):
    knob = nuke.thisNode()[knob_name]
    knob.setEnabled(False)  # Trick pour rafraîchir l'UI
    knob.setEnabled(True)






#------------------------------------------------------------------------------#
#------------------------------------------------------------------- ENTRYPOINT --#

# Automatically link this script to the gizmo
def register_contribution():
    """Register the gizmo and ensure the script is loaded."""
    nuke.addOnUserCreate(knobChanged, nodeClass="contribution")

def initialize_knobs(node):
    light_shuffle_node = node.node("light_shuffle")
    contribution_shuffle_node = node.node("contribution_shuffle")

    if light_shuffle_node and light_shuffle_node.knobs().get("in"):
        light_shuffle_node["in"].setValue("none")

    if contribution_shuffle_node and contribution_shuffle_node.knobs().get("in"):
        contribution_shuffle_node["in"].setValue("none")


nuke.addOnCreate(initialize_knobs, nodeClass="contribution")