import bpy

# custom ui imports
from bpy.props import BoolProperty, EnumProperty, IntProperty, PointerProperty
from bpy.types import Operator, Panel, PropertyGroup
from bpy.utils import register_class, unregister_class

from ...places.utils.checkers import is_non_pano_camera
from ..clean_and_render_place.clean_and_render_place import clean_and_render_place

from ..place_info import place_info
from ..places import setup_place

from ...utils.getters.get_things import get_collections
from ..collection_instances import focus_instance
from ..utils.getters.get_cam_floor_point import get_cam_floor_point
from ..make_cam_frustum_mesh import make_cam_frustum_mesh
from ..make_camcube import make_camcube
from ..custom_props import custom_props_classes

# -------------------------------------------------
# Adding tool panel stuff
# -------------------------------------------------

# Handlers


def on_update_show_camcubes(self, context):
    collections = get_collections()

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
        name="Make backdrops", description="Render backdrops?", default=False
    )
    should_overwrite_render: BoolProperty(
        name="Overwrite renders",
        description="If false, only missing backdrops / hdr images are rendered",
        default=False,
    )
    should_convert_probes: BoolProperty(
        name="Convert probes",
        description="Convert the .hdr to .ennv for babylonjs",
        default=False,
    )
    should_make_details_gltf: BoolProperty(
        name="Export details gtlf",
        description="To use to generate camcubes with gltf2prendy",
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
        default="12",
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
        render_tool_info = scene.render_tool_info
        setup_place(
            int(render_tool_info.my_framerate_enum),
        )
        return {"FINISHED"}


class RenderTools_Operator_RenderVideos(Operator):
    bl_label = "Rerender videos"
    bl_idname = "wm.render_videos"

    def execute(self, context):
        scene = context.scene
        render_tool_info = scene.render_tool_info
        clean_and_render_place(
            render_tool_info.should_rerender,
            render_tool_info.should_overwrite_render,
            render_tool_info.should_convert_probes,
            render_tool_info.the_best_lighting_frame,
            render_tool_info.should_make_details_gltf,
        )
        return {"FINISHED"}


class RenderTools_Operator_MakeCamFrustumMesh(Operator):
    bl_label = "Make Camera Frustum Mesh"
    bl_idname = "wm.make_camera_frustum_mesh"

    def execute(self, context):
        scene = context.scene
        render_tool_info = scene.render_tool_info  # to use properties set in the ui
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


class RenderTools_Operator_GoToInstance(Operator):
    bl_label = "Go To Instance"
    bl_idname = "wm.go_to_instance"

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
        mytool = scene.render_tool_info

        layout.operator("wm.setup_place", text="Setup Place", icon="SHADERFX")
        layout.operator("wm.render_videos", text="Make Place", icon="SCENE")
        layout.prop(mytool, "should_rerender")
        layout.prop(mytool, "should_overwrite_render")
        layout.prop(mytool, "should_convert_probes")
        layout.prop(mytool, "should_make_details_gltf")
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
            "wm.go_to_instance",
            text="Go To Instance",
            icon="OUTLINER_OB_GREASEPENCIL",
        )


# ------------------------------------------------------------------------
#    GUI Registration
# ------------------------------------------------------------------------


# -------------------------------------------------
# Cameras ----------------------------------------
# -------------------------------------------------

# Toggle Segments for Cams --------------------------


class SegmentToggle_Panel(bpy.types.Panel):
    bl_label = "Toggle Segments Panel"
    bl_idname = "OBJECT_PT_toggle_segments"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return is_non_pano_camera(context.object)

    def draw(self, context):
        layout = self.layout
        cam_object = context.object
        cam_data = cam_object.data

        for item in cam_data.cam_segment_infos:
            box = layout.box()
            row = box.row(align=True)
            # Display the segment name as a label (read-only)
            row.label(text=item.segment_name)
            # Display the framerate dropdown and can_render checkbox
            row.prop(item, "framerate", text="FPS")
            row.prop(item, "can_render", text="Render")

        # Remove or adjust this line if 'toggle_all_segments' is not defined
        layout.prop(cam_data, "toggle_all_segments", text="Toggle All")

    bl_label = "Toggle Segments Panel"
    bl_idname = "OBJECT_PT_toggle_segments"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"


def toggle_all_segments(self, context):
    # Loop through cam_data.cam_segment_infos
    for item in self.cam_segment_infos:
        item.can_render = self.toggle_all_segments
    return None


classes = (
    # properties
    RenderTools_Properties,  # This is similar to place info
    #  buttons
    RenderTools_Operator_SetupPlace,
    RenderTools_Operator_RenderVideos,
    RenderTools_Operator_MakeCamFrustumMesh,
    RenderTools_Operator_CheckCamFloorPoint,
    # panels
    RenderTools_Panel,
    SegmentToggle_Panel,
    RenderTools_Operator_MakeCameraCube,
    RenderTools_Operator_GoToInstance,
)

all_classes = classes + tuple(custom_props_classes)


def register_places():

    for the_class in all_classes:
        register_class(the_class)

    bpy.types.Scene.render_tool_info = PointerProperty(type=RenderTools_Properties)
    bpy.types.Camera.toggle_all_segments = BoolProperty(update=toggle_all_segments)


def unregister_places():
    for the_class in reversed(all_classes):
        unregister_class(the_class)
    del bpy.types.Scene.render_tool_info
    del bpy.types.Camera.toggle_all_segments
