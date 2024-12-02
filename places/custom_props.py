from dataclasses import dataclass, field
from typing import Dict, List, TypeAlias

import bpy
from bpy.props import (
    BoolProperty,
    IntProperty,
    StringProperty,
    CollectionProperty,
    EnumProperty,
)

from ..utils.getters.get_things import make_empty_field

# Custom properties for Blender objects


# Define a PropertyGroup for string items to use in CollectionProperty
class StringItem(bpy.types.PropertyGroup):
    value: StringProperty(name="Value", default="")


# NOTE this is also the new way to store 'segments for cams', with can_render
class CamSegmentProps(bpy.types.PropertyGroup):
    segment_name: StringProperty(name="Segment name", default="")
    framerate: EnumProperty(
        name="Framerate",
        description="Choose one of the framerates",
        items=[
            ("60", "60", ""),
            ("30", "30", ""),
            ("24", "24", ""),
            ("20", "20", ""),
            ("15", "15", ""),
            ("12", "12", ""),
            ("10", "10", ""),
            ("6", "6", ""),
            ("5", "5", ""),
            ("3", "3", ""),
            ("2", "2", ""),
            ("1", "1", "Good for trying stuff out"),
        ],
        default="12",
    )
    can_render: BoolProperty(name="Can render", default=False)
    # NOTE Convert the framerate to an int when needed with
    # framerate_value = int(item.framerate)


# NOTE  unused but if new properties are added for meshes, then can swap to this
class MeshExtraProps(bpy.types.PropertyGroup):
    hidden_to_cams: CollectionProperty(
        type=StringItem
    )  # NOTE  the options should be limited to the camera names


custom_props_classes = [StringItem, CamSegmentProps, MeshExtraProps]
