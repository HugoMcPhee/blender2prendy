from ..dump import dump
from ..get_things import get_scene
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


# loop through all the floors , and get the ray
# get_ray_point_for_object(direction, from point)   #hopefully converting global to local position works for any points
# if none of them got a ray point (including if it went past max distance)
# then do the thing getting the xy position infrot of the camera at 10 meters, and do a ray going down on all the floor meshes
#  if that's successful, use the first point found as the point
#  if not, use the 15 meters infront of the camera directly thing


# for looped_object in collections["floors"].objects:
#         if looped_object.type == "MESH":
#             looped_object.name = "floor" + "_" + str(child_floor_counter)
#             floor_names.append(looped_object.name)
#             child_floor_counter += 1


def get_cam_floor_point(context, camera):

    # make sure you have a Camera and an Empty named like this
    scene = context.scene
    camera = bpy.data.objects["Camera"]
    empty = bpy.data.objects["Empty"]
    selected_object = context.active_object

    print("_________________")
    print(selected_object.name)
    # dump(selected_object)

    # object_matrix_world_with_scale_and_rotation = get_applied_world_matrix(
    #     selected_object
    # )
    # matrixWorld = object_matrix_world_with_scale_and_rotation

    # for some reason, the matrix converting thing isn't working... , so applying rotation and scale
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    matrixWorld = selected_object.matrix_world

    cam_direction = camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))

    # calculate origin
    matrixWorldInverted = matrixWorld.inverted()

    # different ways of getting the local-to-object position of the camera
    local_cam_position_a = matrixWorldInverted @ camera.location
    local_cam_position_b = matrixWorldInverted @ camera.matrix_world.translation
    local_cam_position_c = (
        camera.location - selected_object.location
    ) @ matrixWorldInverted

    result, location, normal, index = selected_object.ray_cast(
        local_cam_position_c, cam_direction
    )
    print(location)
    empty.location = matrixWorld @ location

    # Another way to get the cam_direction taken from the automatically placing probes script
    # distz = Vector((0.0, 0.0, -1))
    # camRotationMAT = camera.rotation_euler.to_matrix()
    # camRotationMAT.invert()
    # # project the vector to the world using the rotation matrix
    # cam_direction = distz @ camRotationMAT

    # another way to get a vector
    # direction = mod.location - camera.location;
    # direction.normalize()
