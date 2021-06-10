from .get_point_infront_of_cam import get_point_infront_of_cam
from ..dump import dump
from ..get_things import get_collections, get_scene
from ..get_applied_world_matrix import get_applied_world_matrix
import bpy
import bmesh
from mathutils.bvhtree import BVHTree
import mathutils
from mathutils import Vector, Matrix, Quaternion
import time


# the epsilon value for the BVHTree calculations
EPSILON = 0.00001

# maximum ray distance from camera
MAX_DIRECT_DISTANCE = 50
CHECK_FLOOR_FROM_CAM_DISTANCE = 10
CAM_DISTANCE_FOR_DEFAULT_NO_POINT = 15


# can use for knowing the z position of an auto cam cube, or for an auto probe position :)


def get_ray_point_for_object(direction, from_point, the_object, max_distance=2000):

    print(direction)
    # object_matrix_world_with_scale_and_rotation = get_applied_world_matrix(
    #     the_object
    # )
    # matrixWorld = object_matrix_world_with_scale_and_rotation
    the_object.select_set(True)
    bpy.context.view_layer.objects.active = the_object

    # for some reason, the matrix converting thing isn't working... , so applying rotation and scale
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    matrixWorld = the_object.matrix_world

    # calculate origin
    matrixWorldInverted = matrixWorld.inverted()

    # different ways of getting the local-to-object position of the camera
    local_from_point_a = matrixWorldInverted @ from_point
    # local_from_point_b = matrixWorldInverted @ camera.matrix_world.translation
    # local_from_point_c = (from_point - the_object.location) @ matrixWorldInverted

    result, location, normal, index = the_object.ray_cast(
        local_from_point_a, direction, distance=max_distance
    )

    if result is False:
        return None
    else:
        ray_world_position = matrixWorld @ location
        return ray_world_position


def get_cam_floor_point(context, camera):

    # loop through all the floors , and get the ray
    # get_ray_point_for_object(direction, from point)   #hopefully converting global to local position works for any points
    # if none of them got a ray point (including if it went past max distance)
    # then do the thing getting the xy position infrot of the camera at 10 meters, and do a ray going down on all the floor meshes
    #  if that's successful, use the first point found as the point
    #  if not, use the 15 meters infront of the camera directly thing

    # make sure you have a Camera and an Empty named like this
    scene = context.scene
    camera = bpy.data.objects["Camera"]
    empty = bpy.data.objects["Empty"]
    empty2 = bpy.data.objects["Empty2"]
    selected_object = context.active_object
    collections = get_collections()

    cam_direction = camera.matrix_world.to_quaternion() @ Vector((0.0, 0.0, -1.0))
    cam_location = camera.location

    found_point = None

    for looped_object in collections["floors"].objects:
        if looped_object.type == "MESH":
            a_floor_mesh = looped_object
            print(f"finding point for {a_floor_mesh.name}")

            floor_found_point = get_ray_point_for_object(
                direction=cam_direction,
                from_point=cam_location,
                the_object=a_floor_mesh,
                max_distance=MAX_DIRECT_DISTANCE,
            )
            if floor_found_point is None:
                print("Didn't find a point!")
            else:
                print("Found a point!")
                found_point = floor_found_point
                empty.location = found_point

    if found_point is not None:
        print("Found atleast a point!")
        empty.location = found_point
    else:
        print("Didn't find any first points!")

        new_point_location_edited = get_point_infront_of_cam(
            camera, CHECK_FLOOR_FROM_CAM_DISTANCE
        )
        # move the point to the same height as the camera (so its infront but at the same height)
        new_point_location_edited.z = camera.location.z
        empty2.location = new_point_location_edited

        down_vector = Vector((0, 0, -1))

        for looped_object in collections["floors"].objects:
            if looped_object.type == "MESH":
                a_floor_mesh = looped_object
                print(f"finding safe point for {a_floor_mesh.name}")

                floor_found_point = get_ray_point_for_object(
                    direction=down_vector,
                    from_point=new_point_location_edited,
                    the_object=a_floor_mesh,
                )
                if floor_found_point is None:
                    print("Didn't find a safe point!")
                else:
                    print("Found a safe point!")
                    found_point = floor_found_point

    if found_point is None:
        print("Didn't find any final points!")
        # get the point 15 meters infront of the camera
        found_point = get_point_infront_of_cam(
            camera, CAM_DISTANCE_FOR_DEFAULT_NO_POINT
        )
    else:
        print("Found atleast a point!")

    empty.location = found_point

    # another way to get a vector
    # direction = mod.location - camera.location;
    # direction.normalize()
