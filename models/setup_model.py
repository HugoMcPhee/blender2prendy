import bpy
from math import radians
from mathutils import Euler, Vector

# from .dump import dump


# -------------------------------------------------
# Setup model stuff
# -------------------------------------------------


def setup_model():

    # get the scene
    scene = bpy.context.scene

    #  Get the first and last frames https://blender.stackexchange.com/a/28007
    first_frame = 9999
    last_frame = -9999
    for action in bpy.data.actions:
        if action.frame_range[1] > last_frame:
            last_frame = int(action.frame_range[1])
        if action.frame_range[0] < first_frame:
            first_frame = int(action.frame_range[0])

    scene.frame_start = first_frame
    scene.frame_end = last_frame

    print(
        f"first frame : {first_frame}\nlast frame : {last_frame}\nduration : {last_frame - first_frame}"
    )

    # allow frame dropping in the viewport so the speed is right :)
    scene.sync_mode = "FRAME_DROP"
