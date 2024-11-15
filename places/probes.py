from math import radians
import bpy
from mathutils import Euler, Vector
from ..utils.getters.get_things import get_collections, get_scene, get_view_layer


def setup_probe_rendering():
    scene = get_scene()

    scene.render.resolution_x = 256
    scene.render.resolution_y = 128

    scene.render.image_settings.file_format = "HDR"
    # scene.node_tree.nodes["Denoise"].use_hdr = True


def setup_camera_probes():
    collections = get_collections()
    # Loop through current cameras and add probes if needed

    for cam_collection in collections["cameras"].children:
        probe_object = None
        camera_object = None
        for child_object in cam_collection.objects:
            if child_object.type == "CAMERA":
                if child_object.data.type == "PANO":
                    probe_object = child_object
                else:
                    child_object.name = cam_collection.name
                    camera_object = child_object
        if probe_object is None:
            bpy.ops.object.camera_add(
                location=[0, 10, 20],
                rotation=[radians(90), radians(0), radians(180)],
            )
            # https://blender.stackexchange.com/questions/132112/whats-the-blender-2-8-command-for-adding-an-object-to-a-collection-using-python
            # our created camera is the active one
            probe_object = bpy.context.active_object
            # Remove (active) object from all collections not used in a scene
            bpy.ops.collection.objects_remove_all()
            # add it to our specific collection
            cam_collection.objects.link(probe_object)
            # https://blender.stackexchange.com/questions/26852/python-move-object-on-local-axis
            # 15 blender units in z-direction
            dist_z = Vector((0.0, 0.0, -15))
            rotationMAT = camera_object.rotation_euler.to_matrix()
            rotationMAT.invert()
            # project the vector to the world using the rotation matrix
            zVector = dist_z @ rotationMAT
            probe_object.location = camera_object.location + zVector
            # probe_object.location = camera_object.location + Vector((0, -3, -2))

        probe_object.rotation_euler = Euler(
            (radians(90), radians(0), radians(180)), "XYZ"
        )
        probe_object.data.type = "PANO"
        probe_object.data.panorama_type = "EQUIRECTANGULAR"
        probe_object.name = f"{camera_object.name}_probe"
        # show an axis instead of the camera
        probe_object.show_axis = True
        probe_object.data.display_size = 0.01

        # add custom properties to the camera
        # camera_object.


def toggle_probe_visible_objects(isToggled=True):
    view_layer = get_view_layer()
    # NOTE HAVE to loop through view_layer ?? , can't loop through collection.children ohwell
    for collection in view_layer.layer_collection.children["Details"].children:
        if collection.name == "visible_to_probe":
            collection.exclude = not isToggled
