import bpy

from ...places.place_info import place_info
from ...places.utils.checkers import is_mesh_or_instance
from ...places.utils.getters.getters import get_limited_cam_names
from ...utils.getters.get_things import get_collections
from ...utils.utils import recursively_loop_collection


def update_hidden_cam_info_for_mesh(object: bpy.types.Object):
    mesh_name = object.name

    hidden_cams_for_mesh = []
    limited_cam_names = get_limited_cam_names()
    for cam_index, camera_name in enumerate(limited_cam_names):
        should_hide_for_cam = object.hidden_to_cam_toggles[cam_index]

        if should_hide_for_cam:
            hidden_cams_for_mesh.append(camera_name)
            if not camera_name in place_info.hidden_meshes_by_cam:
                place_info.hidden_meshes_by_cam[camera_name] = []
            place_info.hidden_meshes_by_cam[camera_name].append(mesh_name)

    place_info.hidden_to_cams_by_mesh[mesh_name] = hidden_cams_for_mesh


def update_info_for_meshes(top_collection, levels=10):
    recursively_loop_collection(
        top_collection,
        is_mesh_or_instance,
        update_hidden_cam_info_for_mesh,
        levels=10,
    )


def mesh_to_secret_wireframe(mesh_object):
    mesh_object.display_type = "WIRE"
    mesh_object.visible_camera = True
    mesh_object.visible_camera = False
    mesh_object.visible_diffuse = False
    mesh_object.visible_glossy = False
    mesh_object.visible_transmission = False
    mesh_object.visible_volume_scatter = False
    mesh_object.visible_shadow = False


# NOTE maybe rename this since it's working with blender meshes instead of a prendy thing
def setup_mesh_objects():
    collections = get_collections()

    update_info_for_meshes(collections["Details"])
