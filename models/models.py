import bpy
from bpy.props import IntProperty, EnumProperty, PointerProperty
from bpy.types import Panel, Operator, PropertyGroup
from .make_lowpoly import make_lowpoly
from .setup_model import setup_model
from .export_model import export_model


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------


class RenderModelTools_Properties(PropertyGroup):
    """Properties for rendering the model tools."""

    the_target_polys: IntProperty(
        name="Poly Amount",
        description="How many polygons should the model have?",
        default=4000,
        min=1,
        max=40000,
    )

    texture_sizes = [
        ("1024", "1024", ""),
        ("512", "512", ""),
        ("256", "256", ""),
        ("128", "128", ""),
        ("64", "64", ""),
    ]

    the_color_tex_size: EnumProperty(
        name="Texture Size",
        description="choose one of the color texture sizes",
        items=texture_sizes,
    )
    the_normal_tex_size: EnumProperty(
        name="Normal texture size",
        description="choose one of the texture sizes",
        items=texture_sizes,
    )


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------


class RenderModelTools_Operator_SetupModel(Operator):
    bl_label = "Setup model"
    bl_idname = "wm.setup_model"

    def execute(self, context):
        setup_model()
        print("setting up done :) 🌷")
        return {"FINISHED"}


class RenderModelTools_Operator_ExportModel(Operator):
    bl_label = "Export model"
    bl_idname = "wm.export_model"

    def execute(self, context):
        export_model()
        print("exporting model done :) 🌷")
        return {"FINISHED"}


class RenderModelTools_Operator_MakeLowpoly(Operator):
    bl_label = "Make lowpoly"
    bl_idname = "wm.make_lowpoly"

    def execute(self, context):
        scene = context.scene
        my_models_tool = scene.my_models_tool
        make_lowpoly(
            int(my_models_tool.the_color_tex_size), my_models_tool.the_target_polys
        )

        print("making lowpoly done :) 🌷")
        return {"FINISHED"}


# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------


class RenderModelTools_Panel(Panel):
    bl_label = "Model Exporting"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        my_models_tool = scene.my_models_tool

        # GHOST_ENABLED
        # GHOST_DISABLED
        layout.operator("wm.setup_model", text="Setup Model", icon="SHADERFX")
        layout.operator(
            "wm.export_model", text="Save Model", icon="OUTLINER_OB_ARMATURE"
        )
        layout.separator()
        layout.prop(my_models_tool, "the_color_tex_size")
        layout.prop(my_models_tool, "the_target_polys")
        layout.operator(
            "wm.make_lowpoly", text="Make Lowpoly", icon="OUTLINER_OB_ARMATURE"
        )
        layout.separator()


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    RenderModelTools_Properties,
    RenderModelTools_Operator_SetupModel,
    RenderModelTools_Operator_ExportModel,
    RenderModelTools_Operator_MakeLowpoly,
    RenderModelTools_Panel,
)


def register_models():
    """Registers the model tools in Blender."""
    print("Registering model tools...")
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_models_tool = PointerProperty(type=RenderModelTools_Properties)


def unregister_models():
    """Unregisters the model tools from Blender."""
    print("Unregistering model tools...")
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Scene.my_models_tool
