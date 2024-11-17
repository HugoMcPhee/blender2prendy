import bpy

from .place_info import PlaceInfo, place_info


# not needed! might help if stopping "make backdrops" before it finshed
def reenable_all_meshes():
    for cam_name in place_info.hidden_meshes_by_cam:
        for mesh_name in place_info.hidden_meshes_by_cam[cam_name]:
            mesh_object = bpy.data.objects[mesh_name]
            mesh_object.hide_render = False
            mesh_object.visible_camera = True


def reenable_hidden_meshes():
    # re-enable previously hidden meshes
    for mesh_name in place_info.meshnames_that_were_disabled_in_render:
        mesh_object = bpy.data.objects[mesh_name]
        mesh_object.visible_camera = True
        mesh_object.hide_render = False
    place_info.meshnames_that_were_disabled_in_render = []


def hide_meshes_for_camera(cam_name, is_depth=False):
    # hide meshes to camera that should be hidden
    if cam_name in place_info.hidden_meshes_by_cam:
        for mesh_name in place_info.hidden_meshes_by_cam[cam_name]:
            print(mesh_name)
            mesh_object = bpy.data.objects[mesh_name]
            if is_depth:
                mesh_object.hide_render = True
            else:
                mesh_object.visible_camera = False
            place_info.meshnames_that_were_disabled_in_render.append(mesh_name)
    else:
        print(f"{cam_name} has no hidden meshes :)")
