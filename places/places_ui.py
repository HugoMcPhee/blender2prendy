import bpy

# custom ui imports
from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
from bpy.utils import register_class, unregister_class
from .clean_and_render_place import clean_and_render_place

from .place_info import place_info
from .places import setup_place

from ..get_things import get_collections
from .collection_instances import focus_instance
from .get_cam_floor_point import get_cam_floor_point
from .make_cam_frustum_mesh import make_cam_frustum_mesh
from .make_camcube import make_camcube

# -------------------------------------------------
# Adding tool panel stuff
# -------------------------------------------------


def on_update_show_camcubes(self, context):
    collections = get_collections()
    # update_blender_refs()
    for looped_collection in collections["cameras"].children:
        for looped_cam_box in looped_collection.objects:
            # hide or show each camera collider mesh
            if looped_cam_box.type == "MESH":
                looped_cam_box.hide_set(not self.show_camcubes)
                looped_cam_box.hide_render = not self.show_camcubes


# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------


class RenderTools_Properties(PropertyGroup):
    should_rerender: BoolProperty(
        name="Make videos", description="Render videos?", default=False
    )
    should_overwrite_render: BoolProperty(
        name="Overwrite renders",
        description="If false, only missing videos / hdr images are rendered",
        default=False,
    )
    should_convert_probes: BoolProperty(
        name="Convert probes",
        description="Convert the .hdr to .ennv for babylonjs",
        default=False,
    )

    the_framerate: IntProperty(
        name="Framerate", description="The Video framerate", default=12, min=1, max=60
    )
    the_render_quality: IntProperty(
        name="Quality", description="The render samples", default=2, min=1, max=500
    )
    the_best_lighting_frame: IntProperty(
        name="Best lighting frame",
        description="The frame to render the lighting probes from",
        default=12,
        min=0,
        max=500,
    )
    my_framerate_enum: EnumProperty(
        name="framerate",
        description="choose one of the framerates",
        items=[
            ("60", "60", ""),
            ("30", "30", ""),
            ("20", "20", ""),
            ("15", "15", ""),
            ("12", "12", ""),
            ("10", "10", ""),
            ("6", "6", ""),
            ("5", "5", ""),
            ("3", "3", ""),
            ("2", "2", ""),
            ("1", "1", "good for trying stuff out"),
        ],
    )
    show_camcubes: BoolProperty(
        name="show camera cubes",
        description="show/hide the camera collision meshes",
        default=True,
        update=on_update_show_camcubes,
    )


# ------------------------------------------------------------------------
#    Operators (buttons)
# ------------------------------------------------------------------------


class RenderTools_Operator_SetupPlace(Operator):
    bl_label = "Setup Place"
    bl_idname = "wm.setup_place"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        setup_place(
            place_info, mytool.the_render_quality, int(mytool.my_framerate_enum)
        )
        return {"FINISHED"}


class RenderTools_Operator_RenderVideos(Operator):
    bl_label = "Rerender videos"
    bl_idname = "wm.render_videos"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        clean_and_render_place(
            place_info,
            mytool.should_rerender,
            mytool.should_overwrite_render,
            mytool.should_convert_probes,
            mytool.the_best_lighting_frame,
        )
        return {"FINISHED"}


class RenderTools_Operator_MakeCamFrustumMesh(Operator):
    bl_label = "Make Camera Frustum Mesh"
    bl_idname = "wm.make_camera_frustum_mesh"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool  # to use properties set in the ui
        make_cam_frustum_mesh(scene.camera)
        return {"FINISHED"}


class RenderTools_Operator_CheckCamFloorPoint(Operator):
    bl_label = "Check Camera Floor Point"
    bl_idname = "wm.make_check_camera_floor_point"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        get_cam_floor_point(scene.camera)
        return {"FINISHED"}


class RenderTools_Operator_MakeCameraCube(Operator):
    bl_label = "Make Camera Cube"
    bl_idname = "wm.make_camera_cube"

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        make_camcube(scene.camera)
        return {"FINISHED"}


class RenderTools_Operator_TryNewScript(Operator):
    bl_label = "Try New Script"
    bl_idname = "wm.try_new_script"

    # @classmethod
    # def poll(cls, context):
    #     return context.active_object is not None

    def execute(self, context):
        scene = context.scene
        print("test")
        focus_instance()
        # convert_wall_curves(scene.camera)
        return {"FINISHED"}


# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------


class RenderTools_Panel(Panel):
    # Video Backdrops
    bl_label = "Place Exporting"
    bl_idname = "OBJECT_PT_rendertools_panel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        layout.operator("wm.setup_place", text="Setup Place", icon="SHADERFX")
        layout.operator("wm.render_videos", text="Make Place", icon="SCENE")
        layout.prop(mytool, "should_rerender")
        layout.prop(mytool, "should_overwrite_render")
        layout.prop(mytool, "should_convert_probes")
        layout.separator()
        layout.prop(mytool, "my_framerate_enum")
        layout.prop(mytool, "the_render_quality")
        layout.separator()
        layout.prop(mytool, "the_best_lighting_frame")
        layout.separator()
        layout.prop(mytool, "show_camcubes")
        # trying
        layout.operator(
            "wm.make_camera_frustum_mesh",
            text="Make Camera Frustum Mesh",
            icon="VIEW_CAMERA",
        )
        layout.operator(
            "wm.make_check_camera_floor_point",
            text="Make Check Camera Floor Point",
            icon="VIEW_CAMERA",
        )
        layout.operator(
            "wm.make_camera_cube",
            text="Make Camera Cube",
            icon="VIEW_CAMERA",
        )
        layout.operator(
            "wm.try_new_script",
            text="Try New Script",
            icon="OUTLINER_OB_GREASEPENCIL",
        )


# ------------------------------------------------------------------------
#    GUI Registration
# ------------------------------------------------------------------------


# Toggle Segments for Cams --------------------------


def toggle_all_segments(self, context):
    for i, flag in enumerate(self.segment_toggles):
        self.segment_toggles[i] = self.toggle_all_segments
    return None


class SegmentTogglePanel(bpy.types.Panel):
    """Creates a Panel in the Object properties window"""

    bl_label = "Toggle Segments Panel"
    bl_idname = "OBJECT_PT_toggle_segments"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        theObject = context.object
        should_show = theObject.type == "CAMERA" and theObject.data.type != "PANO"
        return should_show

    def draw(self, context):
        layout = self.layout
        column = layout.column()

        theObject = context.object
        camera_object = None

        if theObject.type == "CAMERA" and theObject.data.type != "PANO":
            camera_object = theObject

            column.prop(camera_object, "toggle_all_segments", text="SELECT ALL")
            column = layout.column(align=True)
            for i, name in enumerate(place_info.segments_order):
                column.prop(
                    camera_object, "segment_toggles", index=i, text=name, toggle=True
                )


# Toggle Mesh visiblity for Cams --------------------------
# allow each mesh to be turned off for a camera
def toggle_all_hidden_to_cams(self, context):
    for i, flag in enumerate(self.hidden_to_cam_toggles):
        self.hidden_to_cam_toggles[i] = self.toggle_all_hidden_to_cams
    return None


class HiddenToCamTogglePanel(bpy.types.Panel):
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

        theObject = context.object
        mesh_object = None

        if theObject.type == "MESH" or theObject.instance_type == "COLLECTION":
            mesh_object = theObject
            column.prop(mesh_object, "toggle_all_hidden_to_cams", text="SELECT ALL")
            column = layout.column(align=True)
            for i, name in enumerate(place_info.camera_names):
                column.prop(
                    mesh_object,
                    "hidden_to_cam_toggles",
                    index=i,
                    text=name,
                    toggle=True,
                )


classes = (
    # properties
    RenderTools_Properties,
    #  buttons
    RenderTools_Operator_SetupPlace,
    RenderTools_Operator_RenderVideos,
    RenderTools_Operator_MakeCamFrustumMesh,
    RenderTools_Operator_CheckCamFloorPoint,
    # panels
    RenderTools_Panel,
    SegmentTogglePanel,
    HiddenToCamTogglePanel,
    RenderTools_Operator_MakeCameraCube,
    RenderTools_Operator_TryNewScript,
)


def register_places():
    for loopedClass in classes:
        register_class(loopedClass)

    bpy.types.Scene.my_tool = PointerProperty(type=RenderTools_Properties)
    bpy.types.Object.toggle_all_segments = BoolProperty(update=toggle_all_segments)

    # Adding custom camera props
    bpy.types.Camera.my_prop = bpy.props.BoolProperty(
        name="My Property", description="This is my bpy.props boolean prop"
    )


def unregister_places():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool
