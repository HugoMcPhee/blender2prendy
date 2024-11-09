import bpy
from bpy.types import Object


def is_non_pano_camera(object: bpy.types.Object) -> bool:
    return object.type == "CAMERA" and object.data.type != "PANO"


def is_cam_focus_point(object: bpy.types.Object) -> bool:
    return object.type == "EMPTY" and "focus" in object.name


def is_start_name(name):
    return name == "start"


def is_mesh_or_instance(object: bpy.types.Object) -> bool:
    is_object = hasattr(object, "type")
    if not is_object:
        return False

    return object.type == "MESH" or object.instance_type == "COLLECTION"
