import bpy

from .place_info import PlaceInfo


# not needed! might help if stopping "make videos" before it finshed
def reenable_all_meshes(place_info: PlaceInfo):
    for cam_name in place_info.hidden_meshes_for_cams:
        for mesh_name in place_info.hidden_meshes_for_cams[cam_name]:
            mesh_object = bpy.data.objects[mesh_name]
            mesh_object.hide_render = False
            mesh_object.visible_camera = True


def reenable_hidden_meshes(place_info: PlaceInfo):
    # re-enable previously hidden meshes
    for mesh_name in place_info.meshnames_that_were_disabled_in_render:
        mesh_object = bpy.data.objects[mesh_name]
        mesh_object.visible_camera = True
        mesh_object.hide_render = False
    place_info.meshnames_that_were_disabled_in_render = []


def hide_meshes_for_camera(place_info: PlaceInfo, cam_name, isDepth=False):
    # hide meshes to camera that should be hidden
    if cam_name in place_info.hidden_meshes_for_cams:
        for mesh_name in place_info.hidden_meshes_for_cams[cam_name]:
            print(mesh_name)
            mesh_object = bpy.data.objects[mesh_name]
            if isDepth:
                mesh_object.hide_render = True
            else:
                mesh_object.visible_camera = False
            place_info.meshnames_that_were_disabled_in_render.append(mesh_name)
    else:
        print(f"{cam_name} has no hidden meshes :)")
