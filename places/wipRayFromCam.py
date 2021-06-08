from ..get_applied_world_matrix import get_applied_world_matrix
import bpy
import bmesh
from mathutils.bvhtree import BVHTree
import mathutils
from mathutils import Vector, Matrix, Quaternion

# the epsilon value for the BVHTree calculations
EPSILON = 0.00001

# maximum ray distance from camera
MAXIMUM_DISTANCE = 100


# make sure you have a Camera and an Empty named like this
scene = bpy.context.scene
camera = bpy.data.objects["Camera"]
empty = bpy.data.objects["Empty"]
selected_object = bpy.context.object


object_matrix_world_with_scale_and_rotation = get_applied_world_matrix(selected_object)


cam_direction = camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))

# Another way to get the cam_direction taken from the automatically placing probes script
# distz = Vector((0.0, 0.0, -1))
# camRotationMAT = camera.rotation_euler.to_matrix()
# camRotationMAT.invert()
# # project the vector to the world using the rotation matrix
# cam_direction = distz @ camRotationMAT

# another way to get a vector
# direction = mod.location - camera.location;
# direction.normalize()


# calculate origin
# matrixWorld = selected_object.matrix_world
matrixWorld = object_matrix_world_with_scale_and_rotation
matrixWorldInverted = matrixWorld.inverted()

# different ways of getting the local-to-object position of the camera
local_cam_position_a = matrixWorldInverted @ camera.location
local_cam_position_b = matrixWorldInverted @ camera.matrix_world.translation
local_cam_position_c = (
    camera.location - selected_object.location
) @ matrixWorldInverted


result, location, normal, index = selected_object.ray_cast(
    local_cam_position_b, cam_direction
)

empty.location = matrixWorld @ location
