import bpy
import os
from math import radians
from mathutils import Euler, Vector

# from .dump import dump

# -------------------------------------------------
# Export model and code stuff
# -------------------------------------------------


def export_model():
    # get the scene
    scene = bpy.context.scene

    filename = bpy.path.basename(bpy.data.filepath)
    if filename:
        scene.render.filepath = filename

    path = os.path.normpath(bpy.data.filepath)
    parts = path.split(os.sep)

    parent_folder_path = os.sep.join(parts[:-1])
    grandparent_folder_path = os.sep.join(parts[:-2])

    full_filename = parts[-1]
    full_filename_parts = full_filename.split(".")
    filename_name = full_filename_parts[-2]
    this_place_name = filename_name

    # Get model names from folder names (folders with index files)
    model_names = []

    with os.scandir(grandparent_folder_path) as it:
        for entry in it:
            if entry.is_dir():
                looped_model_has_index_file = False
                with os.scandir(
                    f"{grandparent_folder_path}{os.sep}{entry.name}"
                ) as model_folder:
                    for model_file in model_folder:
                        if not model_file.name.startswith(".") and model_file.is_file():
                            if model_file.name.startswith("index"):
                                looped_model_has_index_file = True
                if looped_model_has_index_file:
                    model_names.append(entry.name)

    animation_names = []
    bone_names = []
    mesh_names = []
    material_names = []
    skeleton_name = "sdf"

    # Loop through all selected objects
    for looped_object in bpy.context.selected_objects:

        if looped_object.type == "MESH":
            mesh_names.append(looped_object.name)

        if looped_object.type == "ARMATURE":
            skeleton_name = looped_object.name
            for looped_bone in looped_object.pose.bones:
                print(looped_bone.name)
                bone_names.append(looped_bone.name)

    for looped_action in bpy.data.actions:
        print(looped_action.name)
        print(looped_action.library)
        # https://blender.stackexchange.com/questions/52471/how-to-tell-if-an-object-is-linked-with-another-blend
        if looped_action.library is None and not looped_action.name.startswith("__"):
            animation_names.append(looped_action.name)

    for looped_object in bpy.context.selected_objects:
        #  material filtering from  https://github.com/KhronosGroup/glTF-Blender-IO
        for slot in looped_object.material_slots:
            if slot.material is None:
                continue
            material_names.append(slot.material.name)

    # for looped_material in bpy.data.materials:
    #     print(looped_material.name)
    #     material_names.append(looped_material.name)
    #     break

    # Change active collection To Exportable
    if __name__ == "__main__":
        view_layer = scene.view_layers["View Layer"]

    # Export gltf glb file
    bpy.ops.export_scene.gltf(
        export_format="GLB",
        export_cameras=True,
        export_apply=True,
        export_animations=True,
        export_lights=False,
        use_selection=True,
        filepath=parent_folder_path + os.sep + filename_name + ".glb",
    )

    # Save index file
    with open(parent_folder_path + os.sep + "index.ts", "w") as file:

        file.write(f'import modelFile from "./{this_place_name}.glb";\n\n')

        # animation_names
        # bone_names
        # mesh_names
        # material_names

        # animationNames array
        file.write("export const animationNames = [")
        for looped_name in animation_names:
            file.write(f'\n  "{ looped_name}",')
        if len(animation_names) > 0:
            file.write("\n] as const;\n\n")
        else:
            file.write("\n] as never;\n\n")
        # boneNames array
        file.write("export const boneNames = [")
        for looped_name in bone_names:
            file.write(f'\n  "{ looped_name}",')
        file.write("\n] as const;\n\n")

        # meshNames array
        file.write("export const meshNames = [")
        for looped_name in mesh_names:
            file.write(f'\n  "{ looped_name}",')
        file.write("\n] as const;\n\n")

        # materialNames array
        file.write("export const materialNames = [")
        for looped_name in material_names:
            file.write(f'\n  "{ looped_name}",')
        file.write("\n] as const;\n\n")

        # skeletonName string
        file.write(f'export const skeletonName = "{skeleton_name}" as const;\n\n')

        file.write(
            "export type AnimationName = typeof animationNames[number];\n"
            + "export type BoneName = typeof boneNames[number];\n"
            + "export type MeshName = typeof meshNames[number];\n"
            + "export type MaterialNames = typeof materialNames[number];\n\n"
            + "export type SkeletonName = typeof skeletonName;\n\n"
        )

        file.write(
            "export const modelInfo = {\n"
            + "  modelFile,\n"
            + "  animationNames,\n"
            + "  boneNames,\n"
            + "  meshNames,\n"
            + "  materialNames,\n"
            + "  skeletonName,\n"
            + "};\n"
        )

        # grandparent_folder_path

    # Save all places index file
    with open(grandparent_folder_path + os.sep + "index.ts", "w") as file:

        for looped_name in model_names:
            file.write(
                f'import {{ modelInfo as {looped_name}Info }} from "./{looped_name}";\n'
            )

        file.write("\n")
        file.write("export const modelInfoByName = {\n")

        for looped_name in model_names:
            file.write(f"  {looped_name}: {looped_name}Info,\n")
        file.write("};\n")

        # animation_names
        # bone_names
        # mesh_names
        # material_names

        file.write(
            "\n"
            + "export type ModelName = keyof typeof modelInfoByName;\n\n"
            + "export const modelNames = [\n"
        )

        for looped_name in model_names:
            file.write(f'  "{looped_name}", \n')
        file.write("] as const;\n")

        file.write("\n" + "type ModelInfoByName = typeof modelInfoByName;\n\n")

        file.write(
            "export type AnimationNameByModel = {\n"
            + '  [P_ModelName in ModelName]: ModelInfoByName[P_ModelName]["animationNames"][number];\n'
            + "};\n"
            + "export type AnyAnimationName = AnimationNameByModel[ModelName];\n\n"
        )

        file.write(
            "export type BoneNameByModel = {\n"
            + '  [P_ModelName in ModelName]: ModelInfoByName[P_ModelName]["boneNames"][number];\n'
            + "};\n"
            + "export type AnyBoneName = BoneNameByModel[ModelName];\n\n"
        )

        file.write(
            "export type MeshNameByModel = {\n"
            + '  [P_ModelName in ModelName]: ModelInfoByName[P_ModelName]["meshNames"][number];\n'
            + "};\n"
            + "export type AnyMeshName = MeshNameByModel[ModelName];\n\n"
        )

        file.write(
            "export type MaterialNameByModel = {\n"
            + '  [P_ModelName in ModelName]: ModelInfoByName[P_ModelName]["materialNames"][number];\n'
            + "};\n"
            + "export type AnyMaterialName = MaterialNameByModel[ModelName];\n\n"
        )

        file.write(
            "export type SkeletonNameByModel = {\n"
            + '  [P_ModelName in ModelName]: ModelInfoByName[P_ModelName]["skeletonName"];\n'
            + "};\n"
            + "export type AnySkeletonName = SkeletonNameByModel[ModelName];\n\n"
        )

        file.write("\n" + "export const allAnimationNames = [\n")
        for looped_name in model_names:
            file.write(f"  ...{looped_name}Info.animationNames,\n")
        file.write("];\n")

    print("all done :) ⭐")
