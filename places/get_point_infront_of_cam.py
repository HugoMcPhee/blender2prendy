from ..dump import dump
from ..get_things import get_collections, get_scene
from ..get_applied_world_matrix import get_applied_world_matrix
import bpy
import bmesh
from mathutils.bvhtree import BVHTree
import mathutils
from mathutils import Vector, Matrix, Quaternion
import time


def get_point_infront_of_cam(camera, distance):
    dist_z = Vector((0.0, 0.0, -distance))
    camRotationMatrix = camera.rotation_euler.to_matrix()
    camRotationMatrix.invert()
    # project the vector to the world using the rotation matrix
    z_vector = dist_z @ camRotationMatrix
    new_point_location = camera.location + z_vector
    return new_point_location
