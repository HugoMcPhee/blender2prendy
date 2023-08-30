import bpy
from ..get_things import get_collections, get_scene, get_view_layer


def setup_cam_background():
    scene = get_scene()

    try:
        # get background image struct
        active_cam = scene.camera.name
        bg_images = bpy.data.objects[active_cam].data.background_images.items()
        # get background image data, if it exists in struct
        found_background_image = bg_images[0][1].image
        scene.node_tree.nodes["image_node"].image = found_background_image
        scene.node_tree.nodes["switch_background"].check = True
        scene.render.film_transparent = True
        scene.view_settings.view_transform = "Standard"

        # image_scale = bg_images[0][1].scale
    except:
        scene.node_tree.nodes["switch_background"].check = False
        scene.render.film_transparent = False
        print("No Background Found")
