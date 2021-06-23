import bpy


def select_object(an_object):
    # NOTE need to be in object mode to work
    # deselect eveything
    bpy.ops.object.select_all(action="DESELECT")
    # for ob in bpy.context.selected_objects:
    #     ob.select_set(False)
    # select the looped object
    an_object.select_set(True)
    bpy.context.view_layer.objects.active = an_object
    return an_object
