import bpy

# custom ui imports
from bpy.props import BoolProperty, BoolVectorProperty
from bpy.utils import register_class, unregister_class

from ...places.utils.getters.getters import get_limited_cam_names
from ...utils.getters.get_things import just_return_false
from ...places.place_info import place_info

# TODO: Change it to be a collection, and an item can be added to the collection which is a camera name?


# -------------------------------------------------
# Meshes -----------------------------------------
# -------------------------------------------------


# Toggle Mesh visiblity for Cams -------------------
# allow each mesh to be turned off for a camera
def toggle_all_hidden_to_cams(self, context):
    for index, flag in enumerate(self.hidden_to_cam_toggles):
        self.hidden_to_cam_toggles[index] = self.toggle_all_hidden_to_cams
    return None


class HiddenToCamToggle_Panel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Toggle Hidden To Cams"
    bl_idname = "OBJECT_PT_toggle_hidden_to_cams"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        theObject = context.object

        should_show = (
            theObject.type == "MESH" or theObject.instance_type == "COLLECTION"
        )
        return should_show

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        object = context.object
        mesh_object = None

        if object.type == "MESH" or object.instance_type == "COLLECTION":
            mesh_object = object
            column.prop(mesh_object, "toggle_all_hidden_to_cams", text="Toggle All")
            column = layout.column(align=True)
            for index, name in enumerate(place_info.camera_names):
                column.prop(
                    mesh_object,
                    "hidden_to_cam_toggles",
                    index=index,
                    text=name,
                    toggle=True,
                )


classes = [HiddenToCamToggle_Panel]


def register_mesh_properties(self, context):
    # Add hidden to cams toggles prop to meshes in "Details" collection ------------------
    limited_cam_names = get_limited_cam_names()

    default_hidden_to_cams_toggled = map(just_return_false, limited_cam_names)
    bpy.types.Object.hidden_to_cam_toggles = BoolVectorProperty(
        size=len(limited_cam_names), default=default_hidden_to_cams_toggled
    )


def register_meshes():
    for loopedClass in classes:
        register_class(loopedClass)

    bpy.types.Object.toggle_all_hidden_to_cams = BoolProperty(
        name="Toggle All Hidden To Cams",
        description="Toggle All Hidden To Cams",
        default=False,
        update=toggle_all_hidden_to_cams,
    )

    register_mesh_properties(None, None)

    register_class(HiddenToCamToggle_Panel)
