from mathutils import Vector, Matrix, Quaternion


#  get the matrix_world for an object with rotation and scale applies , wthout applying
# by paleajed at https://stackoverflow.com/questions/17181778/cannot-get-ray-cast-in-blender-to-work
def get_applied_world_matrix(selobj):

    # Rotating / panning / zooming 3D view is handled here.
    # Creates a matrix.
    if selobj.rotation_mode == "AXIS_ANGLE":
        # object rotation_quaternionmode axisangle
        ang, x, y, z = selobj.rotation_axis_angle
        matrix = Matrix.Rotation(-ang, 4, Vector((x, y, z)))
    elif selobj.rotation_mode == "QUATERNION":
        # object rotation_quaternionmode euler
        w, x, y, z = selobj.rotation_quaternion
        x = -x
        y = -y
        z = -z
        quat = Quaternion([w, x, y, z])
        matrix = quat.to_matrix()
        matrix.resize_4x4()
    else:
        # object rotation_quaternionmode euler
        ax, ay, az = selobj.rotation_euler
        mat_rotX = Matrix.Rotation(-ax, 4, "X")
        mat_rotY = Matrix.Rotation(-ay, 4, "Y")
        mat_rotZ = Matrix.Rotation(-az, 4, "Z")
        if selobj.rotation_mode == "XYZ":
            matrix = mat_rotX * mat_rotY * mat_rotZ
        elif selobj.rotation_mode == "XZY":
            matrix = mat_rotX * mat_rotZ * mat_rotY
        elif selobj.rotation_mode == "YXZ":
            matrix = mat_rotY * mat_rotX * mat_rotZ
        elif selobj.rotation_mode == "YZX":
            matrix = mat_rotY * mat_rotZ * mat_rotX
        elif selobj.rotation_mode == "ZXY":
            matrix = mat_rotZ * mat_rotX * mat_rotY
        elif selobj.rotation_mode == "ZYX":
            matrix = mat_rotZ * mat_rotY * mat_rotX
    # handle object scaling
    sx, sy, sz = selobj.scale
    mat_scX = Matrix.Scale(sx, 4, Vector([1, 0, 0]))
    mat_scY = Matrix.Scale(sy, 4, Vector([0, 1, 0]))
    mat_scZ = Matrix.Scale(sz, 4, Vector([0, 0, 1]))
    matrix = mat_scX * mat_scY * mat_scZ * matrix

    return matrix


# or could do this to apply the transform to the selected object
# bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
