from dataclasses import dataclass, field
from typing import Dict, List, TypeAlias

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty, CollectionProperty

from ..utils.getters.get_things import make_empty_field

# Custom properties for Blender objects


# Define a PropertyGroup for string items to use in CollectionProperty
class StringItem(bpy.types.PropertyGroup):
    value: StringProperty(name="Value", default="")


# NOTE this is also the new way to store 'segments for cams', with can_render
class CamSegmentProps(bpy.types.PropertyGroup):
    segment_name: StringProperty(name="Segment name", default="")
    framerate: IntProperty(name="Framerate", default=12)
    can_render: BoolProperty(name="Can render", default=False)


# NOTE  unused but if new properties are added for meshes, then can swap to this
class MeshExtraProps(bpy.types.PropertyGroup):
    hidden_to_cams: CollectionProperty(
        type=StringItem
    )  # NOTE  the options should be limited to the camera names


custom_props_classes = [StringItem, CamSegmentProps, MeshExtraProps]
