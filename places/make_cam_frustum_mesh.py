import bpy
import math


# this script tries to recreate what the camera shows in the viewport (orange pyramid) as a mesh

# the viewport camera looks like a point and a plane, this starts by making the plane


def make_cam_frsutum_mesh():

    scene = bpy.context.scene
    camera = scene.camera

    #  get the height scale for the new plane
    #  like 9/16 for a 16:9 ratio
    height_ratio = scene.render.resolution_y / scene.render.resolution_x

    new_plane = bpy.ops.mesh.primitive_plane_add(
        size=1,
        enter_editmode=False,
        align="WORLD",
        scale=(1, height_ratio, 1),
        location=(camera.location),
        rotation=(camera.rotation_euler),
    )

    # make the plane have the correct aspect ratio (like 16:9)
    # (for some reason, setting scale when creating doesn't work)
    bpy.ops.transform.resize(value=(1, height_ratio, 1), orient_type="LOCAL")

    #  using trigonometry to figure out the plane distance from the camera point
    # (imagine looking from above the camera, and halving it into two right angle triangles)
    #  using half the FOV as the angle, and knowing the length of the OPPOSITE side (0.5) , we can calculate the ADJACENT side (distance from camera point to the camera rectangle shown in the viewport)

    # for the Soh Cah Toa trigonometry stuff, this is half the width of the plane (the plane width is 1)
    opposite = 0.5

    camera.data.lens_unit = "FOV"
    field_of_view = camera.data.angle

    # this is the angle for the trigonometry right angle triangle
    angle_radians = field_of_view / 2
    extrude_distance = opposite / math.tan(angle_radians)

    #  turn on edit mode
    bpy.ops.object.editmode_toggle()
    # select the planes face
    bpy.ops.mesh.select_all(action="SELECT")
    # move it to the same position as the camera rectangle shown in the viewport
    bpy.ops.transform.translate(value=(0, 0, -extrude_distance), orient_type="LOCAL")
    # extrude it backwards to the camera point
    bpy.ops.mesh.extrude_region_move(
        MESH_OT_extrude_region={},
        TRANSFORM_OT_translate={
            "value": (0, 0, extrude_distance),
            "orient_type": "NORMAL",
            "orient_matrix_type": "NORMAL",
            "constraint_axis": (False, False, True),
        },
    )
    # join the extruded face in the middle into one point, so it makes a pyramid shape
    bpy.ops.mesh.merge(type="CENTER")

    # turn off edit mode
    bpy.ops.object.editmode_toggle()

    # now there should be a mesh the same shape as the camera object
    # the new mesh can be scaled to see the camera frustum at a longer distance

    bpy.ops.transform.resize(value=(50, 50, 50))
