import bpy
import os
from math import radians
from mathutils import Euler, Vector

# from .dump import dump
from .setup_model import setup_model
from .export_model import export_model


# -------------------------------------------------
# Adding tool panel stuff
# -------------------------------------------------


from bpy.types import (
    Panel,
    Operator,
)


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------


class WM_OT_SetupModel(Operator):
    bl_label = "Setup model"
    bl_idname = "wm.setup_model"

    def execute(self, context):
        setup_model()
        return {"setting up model done :) 🌷"}


class WM_OT_ExportModel(Operator):
    bl_label = "Export model"
    bl_idname = "wm.export_model"

    def execute(self, context):
        export_model()
        return {"exorting model done :) 🌷"}


# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------


class OBJECT_PT_ModelPanel(Panel):
    bl_label = "Model Exporting"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout

        # GHOST_ENABLED
        # GHOST_DISABLED
        layout.operator("wm.setup_model", text="Setup Model", icon="SHADERFX")
        layout.operator(
            "wm.export_model", text="Save Model", icon="OUTLINER_OB_ARMATURE"
        )
        layout.separator()


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = None


def init_model_tools():
    global classes
    classes = (
        WM_OT_SetupModel,
        WM_OT_ExportModel,
        OBJECT_PT_ModelPanel,
    )


init_model_tools()


def register_models():
    print("auto registering????")
    from bpy.utils import register_class, unregister_class

    for cls in classes:
        register_class(cls)


def unregister_models():
    print("auto unregistering????")
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
