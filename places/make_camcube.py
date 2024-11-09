import bpy
import mathutils
from .utils.getters.get_cam_floor_point import get_cam_floor_point
from .make_cam_frustum_mesh import make_cam_frustum_mesh


extrude_distance = 0.001
camcube_height = 3


# NOTE Can do "edge slide" in blender to make the cam cube shorter without messing with the shape from the camera perspective


# NOTE this requires booltooles addon to work, and wil move to the chrom babylonjs way of making them soon
def make_camcube(camera):
    # return early since bool tools is not installed
    if not bpy.context.preferences.addons.get("booltool"):
        return

    #  get the cam point
    cam_floor_point = get_cam_floor_point(camera)
    #  make a plane called temp_flat_cube
    #  put the plane at the camera point point

    bpy.ops.mesh.primitive_plane_add(
        size=200,
        enter_editmode=False,
        align="WORLD",
        location=cam_floor_point,
        scale=(1, 1, 1),
    )
    print("got to here")
    temp_flat_cube = bpy.context.active_object

    temp_flat_cube.name = "cambox_auto"
    bpy.ops.object.mode_set(mode="EDIT")

    #  in edit mode, select all , and extrude it up a little bit

    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_region_move(
        MESH_OT_extrude_region={},
        TRANSFORM_OT_translate={
            "value": (0, 0, extrude_distance),
            "orient_type": "NORMAL",
            "orient_matrix_type": "NORMAL",
            "constraint_axis": (False, False, True),
        },
    )

    #  exit edit mode
    bpy.ops.object.mode_set(mode="OBJECT")

    #  get the cam frustum object called cam_frustum_mesh
    cam_frustum_mesh = make_cam_frustum_mesh(camera)
    # deselect eveything
    bpy.ops.object.select_all(action="DESELECT")

    # set the cam frustrums origin to the cameras center point, and scale it down a little so the camcube doesnt go right to the edges
    cam_frustum_mesh.select_set(True)
    bpy.context.view_layer.objects.active = cam_frustum_mesh

    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # cam_frustum_mesh.data.transform(mathutils.Matrix.Translation(-cam_floor_point))
    # cam_frustum_mesh.matrix_world.translation += cam_floor_point

    # bpy.ops.transform.resize(value=(0.9, 0.9, 0.9))

    # bpy.ops.transform.resize(
    #     value=(0.9, 0.9, 1),
    #     orient_type="LOCAL",
    # )
    # deselect eveything
    bpy.ops.object.select_all(action="DESELECT")
    #  do the boolean intersection with both and name the new one camcube_auto_camName
    # select the cam_frustum then the cam_cube (and mae the cam_cube active)
    cam_frustum_mesh.select_set(True)
    temp_flat_cube.select_set(True)
    bpy.context.view_layer.objects.active = temp_flat_cube
    bpy.ops.object.modifier_apply(modifier="Auto Boolean")
    # FIXME this requires booltooles addon to work
    # bpy.ops.object.booltool_auto_intersect()
    bpy.context.view_layer.objects.active = temp_flat_cube

    #  make it a little shorted inside the camera visible view, and make it taller
    bpy.ops.transform.resize(
        value=(1, 1, 1000 * camcube_height)
    )  # only making it taller here
    # bpy.ops.transform.resize(value=(0.9, 0.9, 500))
    # bpy.ops.transform.resize(value=(1Z, 1, 500))

    # move it to the same collection as the camera
    # Remove selected objects from all collections
    bpy.ops.collection.objects_remove_all()
    # move the new camcube to the cameras collection
    camera.users_collection[0].objects.link(temp_flat_cube)

    # select the camera again
    bpy.ops.object.select_all(action="DESELECT")
    camera.select_set(True)
    bpy.context.view_layer.objects.active = camera
